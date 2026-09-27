import time
import threading
from typing import Dict, Any, Optional, List
from models.evidence import Evidence


class ResearchQueryCache:
    """
    Thread-safe in-memory cache with TTL (Time-To-Live) for public search and crawl requests.
    Prevents redundant external API calls across repeated parameter evaluations.
    """
    def __init__(self, default_ttl_seconds: int = 1800):  # 30 minutes TTL
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        self.default_ttl = default_ttl_seconds

    def _make_key(self, prefix: str, query: str) -> str:
        return f"{prefix.strip().lower()}:{query.strip().lower()}"

    def get(self, prefix: str, query: str) -> Optional[List[Evidence]]:
        key = self._make_key(prefix, query)
        with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                if time.time() - entry["timestamp"] < self.default_ttl:
                    return [ev.copy() if hasattr(ev, 'copy') else ev for ev in entry["data"]]
                else:
                    del self._cache[key]
        return None

    def set(self, prefix: str, query: str, data: List[Evidence]) -> None:
        key = self._make_key(prefix, query)
        with self._lock:
            self._cache[key] = {
                "timestamp": time.time(),
                "data": [ev.copy() if hasattr(ev, 'copy') else ev for ev in data]
            }

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()


# Global Singleton Research Cache
GLOBAL_RESEARCH_CACHE = ResearchQueryCache()
