from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from redis import asyncio as aioredis

from app.core.config import cache_settings

from .exceptions import cache_exc


async def init_cache() -> None:
    redis = aioredis.from_url(
        url=cache_settings.URL,
        socket_timeout=cache_settings.socket_timeout,
        socket_connect_timeout=cache_settings.socket_connect_timeout,
        max_connections=cache_settings.max_connections,
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
