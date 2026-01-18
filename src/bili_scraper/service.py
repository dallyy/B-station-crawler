import time
import os
import json
import aiohttp
import logging
from aiolimiter import AsyncLimiter
from .keywords import KeywordMatcher
from .search import BiliSearchClient
from .crawler import Crawler
from .persist import Persist
from .utils import KEYWORDS_PATH, DEFAULT_RATE_LIMIT, DEFAULT_OUTPUT_FILE

logger = logging.getLogger(__name__)

async def perform_scrape(keywords_file: str = None, db_path: str = None, 
                        out_path: str = None, rate_limit: int = None) -> dict:
    """Perform a complete scrape: search → match → persist → export.
    
    Overwrites results.json with new results (not append).
    Uses keywords from keywords.txt to filter results.
    """
    started_at = int(time.time())
    out_path = out_path or DEFAULT_OUTPUT_FILE
    
    # Clear results.json before starting scrape
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump([], f, ensure_ascii=False, indent=2)
    
    # Load keywords from file
    kw_file = keywords_file or KEYWORDS_PATH
    if not os.path.exists(kw_file):
        raise ValueError(f"Keywords file not found: {kw_file}")
    
    with open(kw_file, "r", encoding="utf-8") as f:
        keywords = [line.strip() for line in f if line.strip()]
    
    if not keywords:
        raise ValueError(f"No keywords found in {kw_file}")
    
    logger.info(f"Loaded {len(keywords)} keywords: {keywords}")
    
    matcher = KeywordMatcher(keywords)
    
    # Perform search with rate limiting
    limiter = AsyncLimiter(rate_limit or DEFAULT_RATE_LIMIT, 1)
    timeout = aiohttp.ClientTimeout(total=30)
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        search_client = BiliSearchClient(session=session, limiter=limiter)
        crawler = Crawler(search_client=search_client, matcher=matcher)
        logger.info(f"Starting crawl with {len(keywords)} keywords")
        items = await crawler.crawl_all(keywords)
        logger.info(f"Crawled {len(items)} videos matching keywords.txt")
    
    # Persist results
    persist = Persist(db_path=db_path)
    await persist.init()

    # Clean up videos that no longer match current keywords
    await persist.cleanup_unmatched_videos(matcher, started_at)

    for item in items:
        await persist.upsert_video(item, started_at)

    await persist.write_run(started_at, int(time.time()), "success", len(items))
    export_path = await persist.export_json(out_path=out_path or DEFAULT_OUTPUT_FILE)
    await persist.close()
    
    logger.info(f"Scrape complete: {len(items)} videos exported to {export_path}")
    
    return {"processed": len(items), "out": export_path}
