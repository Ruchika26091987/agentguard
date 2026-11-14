import re
from typing import List, Optional, Union

from redis.asyncio import Redis

from agentguard.storage.base import BaseCacheStorage

# Characters with special meaning in Redis glob patterns (SCAN MATCH).
_GLOB_SPECIAL = re.compile(r"([\\*?\[\]])")


def _escape_glob(value: str) -> str:
    """Escape Redis glob metacharacters so ``value`` matches literally."""
    return _GLOB_SPECIAL.sub(r"\\\1", value)


class RedisCacheStorage(BaseCacheStorage):
    """Async Redis cache backend.

    Every key is namespaced with ``key_prefix`` so that ``clear_pattern`` can
    never touch keys owned by other applications sharing the same database.

    Either pass ``redis_url`` (the storage creates and owns the client) or inject
    an existing ``redis.asyncio.Redis`` instance via ``client`` (e.g. a
    ``fakeredis.FakeAsyncRedis`` in tests). An injected client is owned by the
    caller and is not closed by :meth:`close`.
    """

    def __init__(
        self,
        redis_url: Optional[str] = None,
        *,
        client: Optional[Redis] = None,
        key_prefix: str = "agentguard:",
        scan_batch_size: int = 500,
    ):
        if client is not None and redis_url is not None:
            raise ValueError("Pass either redis_url or client, not both")
        if client is None and redis_url is None:
            raise ValueError("Either redis_url or client must be provided")
        if scan_batch_size < 1:
            raise ValueError("scan_batch_size must be >= 1")

        if client is None:
            client = Redis.from_url(redis_url, decode_responses=True)
            self._owns_client = True
        else:
            self._owns_client = False

        self._client = client
        self._key_prefix = key_prefix
        self._scan_batch_size = scan_batch_size

    def _k(self, key: str) -> str:
        return f"{self._key_prefix}{key}"

    async def get(self, key: str) -> Optional[str]:
        value: Union[str, bytes, None] = await self._client.get(self._k(key))
        if isinstance(value, bytes):
            # Injected clients may not use decode_responses=True.
            return value.decode("utf-8")
        return value

    async def set(self, key: str, value: str, ttl_seconds: int) -> None:
        if ttl_seconds <= 0:
            # Redis rejects EX <= 0. Treat it as "already expired", matching
            # InMemoryCacheStorage: the value is not retrievable afterwards.
            await self._client.delete(self._k(key))
            return
        await self._client.set(self._k(key), value, ex=int(ttl_seconds))

    async def delete(self, key: str) -> bool:
        return bool(await self._client.delete(self._k(key)))

    async def clear_pattern(self, pattern: str) -> int:
        """Purge keys whose (un-namespaced) name starts with ``pattern``.

        Same semantics as InMemoryCacheStorage: trailing ``*`` are stripped and
        the remainder is a literal prefix (glob characters inside it are
        escaped). Uses incremental SCAN plus batched UNLINK instead of KEYS, so
        the Redis server is never blocked by a full keyspace walk.
        """
        literal_prefix = self._key_prefix + pattern.rstrip("*")
        if not literal_prefix:
            raise ValueError(
                "Refusing to clear every key in the database: "
                "empty key_prefix and empty pattern"
            )
        match = _escape_glob(literal_prefix) + "*"

        deleted = 0
        batch: List[Union[str, bytes]] = []
        async for key in self._client.scan_iter(
            match=match, count=self._scan_batch_size
        ):
            batch.append(key)
            if len(batch) >= self._scan_batch_size:
                deleted += await self._client.unlink(*batch)
                batch.clear()
        if batch:
            deleted += await self._client.unlink(*batch)
        # UNLINK's return value counts keys actually removed, so duplicates
        # returned by SCAN or keys that expired mid-scan are not double counted.
        return deleted

    async def close(self) -> None:
        """Release the connection pool if this storage created the client."""
        if not self._owns_client:
            return
        aclose = getattr(self._client, "aclose", None)  # redis-py >= 5.0.1
        if aclose is not None:
            await aclose()
        else:
            await self._client.close()
