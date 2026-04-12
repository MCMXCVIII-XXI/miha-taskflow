"""Mock Redis backend for tests with TTL support."""

import time


class MockRedisBackend:
    """In-memory Redis-like backend with TTL support for FastAPICache."""

    def __init__(self):
        self._store: dict[str, tuple[bytes, float | None]] = {}

    async def get(self, key: str) -> bytes | None:
        """Get value by key. Returns None if key doesn't exist or expired."""
        entry = self._store.get(key)
        if entry is None:
            return None
        value, expire = entry
        if expire and time.time() >= expire:
            del self._store[key]
            return None
        return value

    async def set(self, key: str, value: bytes, expire: int | None = None) -> None:
        """Set value with optional TTL (in seconds)."""
        expire_ts = time.time() + expire if expire else None
        self._store[key] = (value, expire_ts)

    async def delete(self, key: str) -> None:
        """Delete key from cache."""
        self._store.pop(key, None)

    async def keys_match(self, pattern: str) -> list[str]:
        """Find keys matching pattern (* or prefix*)."""
        if pattern == "*":
            return list(self._store)
        if pattern.endswith("*"):
            prefix = pattern[:-1]
            return [k for k in self._store if k.startswith(prefix)]
        return [k for k in self._store if k == pattern]

    async def clear(self, namespace: str = "", key: str = "") -> None:
        """Clear cache. Supports clear() or clear(namespace, key)."""
        if namespace and key:
            self._store.pop(key, None)
        elif namespace:
            prefix = f"{namespace}:"
            for k in list(self._store.keys()):
                if k.startswith(prefix):
                    del self._store[k]
        else:
            self._store.clear()
