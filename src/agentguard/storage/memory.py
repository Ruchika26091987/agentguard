import time
from typing import Dict, Optional, Tuple

from agentguard.storage.base import BaseCacheStorage


class InMemoryCacheStorage(BaseCacheStorage):
    def __init__(self):
        self._store: Dict[str, Tuple[str, float]] = {}

    async def get(self, key: str) -> Optional[str]:
        item = self._store.get(key)
        if not item:
            return None
        val, expires_at = item
        if time.time() > expires_at:
            del self._store[key]
            return None
        return val

    async def set(self, key: str, value: str, ttl_seconds: int) -> None:
        self._store[key] = (value, time.time() + ttl_seconds)

    async def delete(self, key: str) -> bool:
        return self._store.pop(key, None) is not None

    async def clear_pattern(self, pattern: str) -> int:
        prefix = pattern.rstrip("*")
        to_del = [k for k in self._store if k.startswith(prefix)]
        for k in to_del:
            del self._store[k]
        return len(to_del)
