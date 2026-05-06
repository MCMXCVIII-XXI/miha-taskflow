"""
SSE (Server-Sent Events) manager module.
"""

import asyncio
import json
from collections import defaultdict
from typing import Any

import redis.asyncio as redis
from loguru import logger

from app.core.config import CacheSettings, cache_settings, sse_settings


class SSEManager:
    """
    Manages SSE (Server-Sent Events) connections and events.
    """

    def __init__(self, cache_settings: CacheSettings):
        self.redis_url = cache_settings.URL
        self._redis: redis.Redis | None = None
        self._pubsub: redis.client.PubSub | None = None
        self._listener_task: asyncio.Task[Any] | None = None

        self._connections: dict[int, asyncio.Queue[str]] = defaultdict(asyncio.Queue)

    async def connect(self, user_id: int) -> asyncio.Queue[str]:
        """User connects to SSE."""
        if user_id not in self._connections:
            self._connections[user_id] = asyncio.Queue(maxsize=100)

        logger.info(f"User {user_id} connected to SSE")
        return self._connections[user_id]

    async def disconnect(self, user_id: int) -> None:
        """User disconnects from SSE."""
        if user_id in self._connections:
            del self._connections[user_id]
            logger.info(f"User {user_id} disconnected from SSE")

    async def publish(
        self, user_id: int, event_type: str, data: dict[str, Any]
    ) -> bool:
        """Publish to Redis + local queue (return True if delivered locally)."""
        message = json.dumps({"event": event_type, "data": data}, default=str)

        if self._redis:
            await self._redis.publish(f"sse:user:{user_id}", message)

        if user_id in self._connections:
            try:
                self._connections[user_id].put_nowait(message)
                return True
            except asyncio.QueueFull:
                logger.warning(f"User {user_id} SSE queue full - dropped")
                return False

        return True

    async def start(self) -> None:
        """Starts the SSE manager (connects to Redis)."""
        if not sse_settings.ENABLED:
            logger.warning("SSE is disabled in settings")
            return

        self._redis = redis.from_url(str(self.redis_url), decode_responses=True)
        self._pubsub = self._redis.pubsub()

        await self._pubsub.psubscribe("sse:user:*")
        self._listener_task = asyncio.create_task(self._listen())

        logger.info("SSE Manager started")

    async def stop(self) -> None:
        """Stops the SSE manager."""
        if self._listener_task:
            self._listener_task.cancel()
            try:
                await self._listener_task
            except asyncio.CancelledError:
                pass

        if self._pubsub:
            await self._pubsub.close()
        if self._redis:
            await self._redis.close()

        logger.info("SSE Manager stopped")

    def health(self) -> dict[str, Any]:
        return {
            "redis_connected": self._redis is not None,
            "pubsub_active": self._pubsub is not None,
            "connections": len(self._connections),
            "listener_alive": self._listener_task is not None
            and not self._listener_task.done(),
        }

    async def _listen(self) -> None:
        """Listens for messages on Redis Pub/Sub channels."""
        if not self._pubsub:
            logger.error("PubSub not initialized")
            return

        async for message in self._pubsub.listen():
            if message["type"] == "pmessage":
                channel = message["channel"]
                user_id = int(channel.split(":")[-1])

                if user_id in self._connections:
                    await self._connections[user_id].put(message["data"])


sse_manager = SSEManager(cache_settings=cache_settings)
