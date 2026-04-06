import asyncio
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from typing import Any

from app.core.config import sse_settings
from app.core.log import get_logger
from app.core.sse import sse_manager

logger = get_logger("service.sse")


class SSEService:
    """Service for SSE."""

    async def connect(self, user_id: int) -> asyncio.Queue[str]:
        """Connect user to SSE."""
        return await sse_manager.connect(user_id)

    async def disconnect(self, user_id: int) -> None:
        """Disconnect user from SSE."""
        await sse_manager.disconnect(user_id)

    async def event_generator(self, user_id: int) -> AsyncGenerator[str, None]:
        """Event generator for StreamingResponse."""
        queue = await self.connect(user_id)

        try:
            while True:
                try:
                    message = await asyncio.wait_for(
                        queue.get(), timeout=sse_settings.HEARTBEAT_INTERVAL
                    )
                    yield "event: notification\n"
                    yield f"data: {message}\n\n"

                except TimeoutError:
                    yield "event: ping\n"
                    yield f'data: \
                        {{"timestamp": "{datetime.now(UTC).isoformat()}"}}\n\n'

        except asyncio.CancelledError:
            pass
        finally:
            await self.disconnect(user_id)

    async def send_notification(
        self, user_id: int, event_type: str, data: dict[str, Any]
    ) -> None:
        """Send notification to user."""
        await sse_manager.publish(
            user_id=user_id,
            event_type="notification",
            data=data,
        )


def get_sse_service() -> SSEService:
    return SSEService()
