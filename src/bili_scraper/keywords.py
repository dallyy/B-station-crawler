import ahocorasick
import asyncio
import html
import re
from typing import List, Set

TAG_RE = re.compile(r"<.*?>")

class KeywordMatcher:
    def __init__(self, keywords: List[str]):
        self.keywords = [k.strip() for k in keywords if k.strip()]
        self.automaton = ahocorasick.Automaton()
        for i, kw in enumerate(self.keywords):
            self.automaton.add_word(kw, (i, kw))
        self.automaton.make_automaton()

    def _normalize(self, text: str) -> str:
        if not text:
            return ""
        text = html.unescape(text)
        text = TAG_RE.sub("", text)
        return text

    def _match_sync(self, text: str) -> Set[str]:
        text = self._normalize(text)
        matches = set()
        for end_index, (idx, kw) in self.automaton.iter(text):
            matches.add(kw)
        return matches

    async def match(self, text: str) -> Set[str]:
        # pyahocorasick is a C extension; run in thread to avoid blocking event loop
        return await asyncio.to_thread(self._match_sync, text)
