from abc import ABC, abstractmethod
from typing import Optional


class BaseCacheStorage(ABC):
    @abstractmethod
    async def get(self, key: str) -> Optional[str]:
        """Fetch serialized item by key."""

    @abstractmethod
    async def set(self, key: str, value: str, ttl_seconds: int) -> None:
        """Store item with expiration in seconds."""

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Invalidate single key."""

    @abstractmethod
    async def clear_pattern(self, pattern: str) -> int:
        """Purge keys matching prefix."""
