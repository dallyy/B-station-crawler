import aiosqlite
import json
import os
from typing import Any, Dict, List
from .utils import DB_PATH, DEFAULT_OUTPUT_FILE
from .keywords import KeywordMatcher

_SCHEMA_INITIALIZED = False
_SCHEMA_LOCK = None

_CREATE_VIDEOS = """
CREATE TABLE IF NOT EXISTS videos (
    bvid TEXT PRIMARY KEY,
    title TEXT,
    pubdate INTEGER,
    url TEXT,
    metadata_json TEXT,
    scraped_at INTEGER,
    hot INTEGER DEFAULT 0
)
"""

_CREATE_RUNS = """
CREATE TABLE IF NOT EXISTS scrape_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at INTEGER,
    finished_at INTEGER,
    status TEXT,
    processed_count INTEGER,
    errors TEXT
)
"""


class Persist:
    def __init__(self, db_path: str = None):
        self.db_path = db_path or DB_PATH
        self.conn = None

    async def init(self):
        """Initialize database connection and schema once."""
        global _SCHEMA_INITIALIZED, _SCHEMA_LOCK
        
        self.conn = await aiosqlite.connect(self.db_path)
        
        if not _SCHEMA_INITIALIZED:
            await self.conn.execute(_CREATE_VIDEOS)
            await self.conn.execute(_CREATE_RUNS)
            
            # Ensure `hot` column exists for older DBs (migration)
            cur = await self.conn.execute("PRAGMA table_info(videos)")
            cols = await cur.fetchall()
            col_names = [c[1] for c in cols]
            if 'hot' not in col_names:
                await self.conn.execute("ALTER TABLE videos ADD COLUMN hot INTEGER DEFAULT 0")
            
            await self.conn.commit()
            _SCHEMA_INITIALIZED = True

    async def close(self):
        await self.conn.close()

    async def upsert_video(self, item: Dict[str, Any], scraped_at: int):
        bvid = item.get("bvid")
        hot = int(item.get("hot") or 0)
        await self.conn.execute(
            "INSERT INTO videos(bvid,title,pubdate,url,metadata_json,scraped_at,hot) VALUES (?,?,?,?,?,?,?)"
            " ON CONFLICT(bvid) DO UPDATE SET title=excluded.title, pubdate=excluded.pubdate, url=excluded.url, metadata_json=excluded.metadata_json, scraped_at=excluded.scraped_at, hot=excluded.hot",
            (bvid, item.get("title"), item.get("pubdate"), item.get("url"), json.dumps(item.get("metadata", {}), ensure_ascii=False), scraped_at, hot),
        )
        await self.conn.commit()

    async def write_run(self, started_at: int, finished_at: int, status: str, processed_count: int, errors: str = ""):
        await self.conn.execute(
            "INSERT INTO scrape_runs(started_at,finished_at,status,processed_count,errors) VALUES (?,?,?,?,?)",
            (started_at, finished_at, status, processed_count, errors),
        )
        await self.conn.commit()

    async def cleanup_unmatched_videos(self, matcher: KeywordMatcher, current_scraped_at: int):
        """Remove videos that no longer match the current keywords configuration."""
        cursor = await self.conn.execute(
            "SELECT bvid, title, metadata_json FROM videos WHERE scraped_at < ?",
            (current_scraped_at,)
        )
        rows = await cursor.fetchall()

        removed_count = 0
        for row in rows:
            bvid, title, metadata_json = row
            metadata = json.loads(metadata_json) if metadata_json else {}
            raw = metadata.get("raw", {})

            # Check if video still matches current keywords
            matches = set()
            title_matches = await matcher.match(title or "")
            matches.update(title_matches)

            desc = raw.get("description") or raw.get("desc") or ""
            if desc:
                desc_matches = await matcher.match(desc)
                matches.update(desc_matches)

            # If no matches found, remove the video
            if not matches:
                await self.conn.execute("DELETE FROM videos WHERE bvid = ?", (bvid,))
                removed_count += 1

        if removed_count > 0:
            await self.conn.commit()

        return removed_count

    async def cleanup_old_videos(self, retention_days: int = 30) -> dict:
        """Clear results.json file (delete its content)."""
        out_path = DEFAULT_OUTPUT_FILE
        try:
            # Write empty JSON array
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump([], f, ensure_ascii=False, indent=2)
            return {"status": "success", "message": "Results cleared", "file": out_path}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def export_json(self, out_path: str = None) -> str:
        """Export all videos to JSON file."""
        out_path = out_path or DEFAULT_OUTPUT_FILE
        cursor = await self.conn.execute(
            "SELECT bvid,title,pubdate,url,metadata_json,scraped_at,COALESCE(hot,0) "
            "FROM videos ORDER BY hot DESC, scraped_at DESC"
        )
        rows = await cursor.fetchall()
        result = []
        for r in rows:
            result.append({
                "bvid": r[0],
                "title": r[1],
                "pubdate": r[2],
                "url": r[3],
                "metadata": json.loads(r[4]) if r[4] else {},
                "scraped_at": r[5],
                "hot": r[6],
            })
        
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        return out_path
