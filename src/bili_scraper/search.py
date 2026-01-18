import aiohttp
import asyncio
from typing import Dict, Any, Optional
from aiolimiter import AsyncLimiter
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from .utils import DEFAULT_HEADERS

SEARCH_URL = "https://api.bilibili.com/x/web-interface/search/type"

class BiliSearchClient:
    def __init__(self, session: aiohttp.ClientSession, limiter: AsyncLimiter):
        self.session = session
        self.limiter = limiter

    @retry(stop=stop_after_attempt(4), wait=wait_exponential(multiplier=1, min=1, max=8),
           retry=retry_if_exception_type(Exception))
    async def search_videos(self, keyword: str, pn: int = 1, ps: int = 20) -> Optional[Dict[str, Any]]:
        params = {
            "search_type": "video",
            "keyword": keyword,
            "pn": pn,
            "ps": ps,
            "order": "pubdate",
        }
        async with self.limiter:
            async with self.session.get(SEARCH_URL, params=params, headers=DEFAULT_HEADERS, timeout=20) as resp:
                if resp.status >= 500:
                    raise Exception(f"Server error: {resp.status}")
                if resp.status == 429:
                    raise Exception("Rate limited (429)")
                if resp.status != 200:
                    # Non-retryable for client errors
                    text = await resp.text()
                    return {"code": resp.status, "text": text}
                data = await resp.json()
                return data
