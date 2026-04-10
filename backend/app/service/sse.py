import asyncio
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from typing import Any

from app.core.config import sse_settings
from app.core.log import get_logger
from app.core.sse import sse_manager

logger = get_logger("service.sse")


class SSEService:
    """Service for Server-Sent Events (SSE) functionality.

    This service handles real-time communication with clients through SSE,
    providing event streaming capabilities for notifications and live updates.
    It manages user connections, event generation, and notification broadcasting.

    Attributes:
        None: This service uses global sse_manager instance for actual operations
    """

    async def connect(self, user_id: int) -> asyncio.Queue[str]:
        """Connect user to SSE event stream.

        Args:
            user_id: ID of user to connect to SSE

        Returns:
            asyncio.Queue[str]: Queue for receiving SSE events for this user
        """
        return await sse_manager.connect(user_id)

    async def disconnect(self, user_id: int) -> None:
        """Disconnect user from SSE event stream.

        Args:
            user_id: ID of user to disconnect from SSE
        """
        await sse_manager.disconnect(user_id)

    async def event_generator(self, user_id: int) -> AsyncGenerator[str, None]:
        """Generate SSE events for a connected user.

        Provides a continuous stream of events including user notifications
        and periodic heartbeat pings to keep the connection alive.

        Args:
            user_id: ID of user to generate events for

        Yields:
            str: Formatted SSE event strings
        """
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
        """Send notification to a specific user via SSE.

        Args:
            user_id: ID of user to send notification to
            event_type: Type of event (typically "notification")
            data: Notification data to send
        """
        await sse_manager.publish(
            user_id=user_id,
            event_type="notification",
            data=data,
        )


def get_sse_service() -> SSEService:
    """Create SSEService instance.

    Returns:
        SSEService: Initialized SSE service instance
    """
    return SSEService()
