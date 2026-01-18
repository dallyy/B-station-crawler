import asyncio
import re
import logging
from typing import List, Dict, Any
from .search import BiliSearchClient
from .keywords import KeywordMatcher
from .utils import DEFAULT_PAGE_SIZE, DEFAULT_MAX_PAGES

logger = logging.getLogger(__name__)


def parse_count(val) -> int:
    """Parse play/like count strings which may include Chinese units (万, 亿), commas, plus signs, or plain numbers.
    Examples: '1.2万' -> 12000, '3.4亿' -> 340000000, '12,345' -> 12345, '5000' -> 5000
    """
    if val is None:
        return 0
    if isinstance(val, (int, float)):
        try:
            return int(val)
        except Exception:
            return 0
    s = str(val).strip()
    if not s:
        return 0
    # remove commas and trailing plus signs
    s = s.replace(',', '').rstrip('+')
    # try direct float conversion first
    try:
        if '亿' in s:
            m = re.search(r'[0-9]+(?:\.[0-9]+)?', s)
            if m:
                return int(float(m.group(0)) * 100000000)
            return 0
        if '万' in s:
            m = re.search(r'[0-9]+(?:\.[0-9]+)?', s)
            if m:
                return int(float(m.group(0)) * 10000)
            return 0
        return int(float(s))
    except Exception:
        # try to extract first number
        m = re.search(r'[0-9]+(?:\.[0-9]+)?', s)
        if m:
            try:
                return int(float(m.group(0)))
            except Exception:
                return 0
    return 0

class Crawler:
    def __init__(self, search_client: BiliSearchClient, matcher: KeywordMatcher, 
                 max_pages: int = None, page_size: int = None):
        self.search_client = search_client
        self.matcher = matcher
        self.max_pages = max_pages or DEFAULT_MAX_PAGES
        self.page_size = page_size or DEFAULT_PAGE_SIZE

    async def _extract_item(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        # raw format expected from search result
        title = raw.get("title") or ""
        # remove possible highlight tags will be handled by matcher.normalize
        bvid = raw.get("bvid") or raw.get("bvid")
        aid = raw.get("aid")
        pubdate = raw.get("pubdate")  # unix seconds
        url = f"https://www.bilibili.com/video/{bvid}" if bvid else raw.get("arcurl")
        # Determine a simple hotness metric: prefer numeric `play`, fallback to `like` or 0
        hot = 0
        try:
            play = raw.get("play") or raw.get("playcount")
            if play is None:
                stat = raw.get("stat") or {}
                play = stat.get("view") or stat.get("play")
            hot = parse_count(play)
            if hot == 0:
                like = raw.get("like") or 0
                hot = parse_count(like)
        except Exception:
            hot = 0
        return {"bvid": bvid, "title": title, "pubdate": pubdate, "url": url, "hot": hot, "raw": raw}

    async def crawl_keyword(self, keyword: str) -> List[Dict[str, Any]]:
        """Search for videos using the keyword and filter by keywords.txt matches."""
        results = []
        seen_bvid = set()
        matched_count = 0
        
        for pn in range(1, self.max_pages + 1):
            data = await self.search_client.search_videos(keyword=keyword, pn=pn, ps=self.page_size)
            if not data or data.get("data") is None:
                break
            result_list = data["data"].get("result") or data["data"].get("vlist") or []
            if not result_list:
                break
            
            for raw in result_list:
                item = await self._extract_item(raw)
                pub = item.get("pubdate")
                if pub is None:
                    continue
                bvid = item.get("bvid")
                if not bvid or bvid in seen_bvid:
                    continue
                seen_bvid.add(bvid)
                
                # STRICT: Match only if keywords.txt keywords are found in title or description
                matches = set()
                title = item.get("title", "")
                title_matches = await self.matcher.match(title)
                matches.update(title_matches)
                desc = raw.get("description") or raw.get("desc") or ""
                if desc:
                    desc_matches = await self.matcher.match(desc)
                    matches.update(desc_matches)
                
                # Only keep if has matches from keywords.txt
                if matches:
                    matched_count += 1
                    hot = int(item.get('hot') or 0)
                    results.append({
                        "bvid": bvid,
                        "title": title,
                        "pubdate": pub,
                        "url": item.get("url"),
                        "matches": sorted(list(matches)),
                        "metadata": {"raw": raw},
                        "hot": hot,
                    })
            # small sleep to be polite
            await asyncio.sleep(0.1)
        
        logger.debug(f"Keyword '{keyword}': matched {matched_count} videos from {len(seen_bvid)} total results")
        return results

    async def crawl_all(self, keywords: List[str]) -> List[Dict[str, Any]]:
        """Crawl all keywords and merge results, removing duplicates."""
        logger.info(f"Starting crawl for {len(keywords)} keywords")
        tasks = [self.crawl_keyword(k) for k in keywords]
        res = await asyncio.gather(*tasks)
        combined = []
        seen = set()
        for lst in res:
            for item in lst:
                if item["bvid"] in seen:
                    continue
                seen.add(item["bvid"])
                combined.append(item)
        logger.info(f"Crawl complete: {len(combined)} unique videos found")
        return combined
