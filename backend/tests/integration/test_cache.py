"""Integration tests for cache (Redis mock)."""

import asyncio

from tests.mock_cache import MockRedisBackend


class TestCacheTTL:
    """Test TTL functionality in MockRedisBackend."""

    async def test_cache_expires_after_ttl(self):
        """Key expires after TTL passes."""

        backend = MockRedisBackend()
        await backend.set("key", b"value", expire=1)

        result = await backend.get("key")
        assert result == b"value"

        await asyncio.sleep(1.1)

        result = await backend.get("key")
        assert result is None

    async def test_cache_no_ttl_never_expires(self):
        """Key without TTL never expires."""

        backend = MockRedisBackend()
        await backend.set("key", b"value")

        await asyncio.sleep(2.0)

        result = await backend.get("key")
        assert result == b"value"


class TestCacheErrors:
    """Test cache error scenarios."""

    async def test_cache_miss_returns_none(self):
        """Non-existent key returns None."""

        backend = MockRedisBackend()
        result = await backend.get("nonexistent")
        assert result is None

    async def test_cache_delete_removes_key(self):
        """Delete removes key from cache."""

        backend = MockRedisBackend()
        await backend.set("key", b"value")
        await backend.delete("key")

        result = await backend.get("key")
        assert result is None

    async def test_cache_keys_match_pattern(self):
        """Keys matching pattern are found."""

        backend = MockRedisBackend()
        await backend.set("user:1", b"value1")
        await backend.set("user:2", b"value2")
        await backend.set("task:1", b"task")

        user_keys = await backend.keys_match("user:*")
        assert len(user_keys) == 2

        all_keys = await backend.keys_match("*")
        assert len(all_keys) == 3
