import asyncio

import pytest

from agentguard.storage.memory import InMemoryCacheStorage


@pytest.mark.asyncio
async def test_memory_storage_ttl():
    storage = InMemoryCacheStorage()
    await storage.set("key1", '{"value": 42}', ttl_seconds=1)
    assert await storage.get("key1") == '{"value": 42}'

    await asyncio.sleep(1.1)
    assert await storage.get("key1") is None


@pytest.mark.asyncio
async def test_memory_storage_clear_pattern():
    storage = InMemoryCacheStorage()
    await storage.set("tool:db:1", "val1", 60)
    await storage.set("tool:db:2", "val2", 60)
    await storage.set("tool:api:1", "val3", 60)

    cleared = await storage.clear_pattern("tool:db:*")
    assert cleared == 2
    assert await storage.get("tool:db:1") is None
    assert await storage.get("tool:api:1") == "val3"
