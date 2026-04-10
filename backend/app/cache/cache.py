"""Initializes FastAPI-Cache with Redis backend for application caching.

This module sets up the Redis caching system for the application including
connection establishment, configuration loading, and error handling.
Provides application-wide caching functionality for performance optimization.
"""

from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from redis import asyncio as aioredis

from app.core.config import cache_settings

from .exceptions import cache_exc


async def init_cache() -> None:
    """Configures and initializes Redis cache backend for the application.

    Establishes connection to Redis server using cache_settings configuration
    and initializes FastAPI-Cache with Redis backend. Performs connection
    validation and handles initialization errors appropriately.

    Raises:
        cache_exc.CacheConnectionError: When Redis connection cannot be established
    """
    redis = aioredis.from_url(
        url=str(cache_settings.URL),
        socket_timeout=cache_settings.SOCKET_TIMEOUT,
        socket_connect_timeout=cache_settings.SOCKET_CONNECT_TIMEOUT,
        max_connections=cache_settings.MAX_CONNECTIONS,
    )
    prefix = "fastapi-cache"

    try:
        ping_result = await redis.ping()  # type: ignore[misc]
        if ping_result:
            FastAPICache.init(RedisBackend(redis), prefix=prefix)
    except aioredis.ConnectionError as e:
        raise cache_exc.CacheConnectionError(
            message="Couldn't connect to Redis.",
            headers={"Retry-After": "30", "X-Error-Type": "CACHE_UNAVAILABLE"},
        ) from e
