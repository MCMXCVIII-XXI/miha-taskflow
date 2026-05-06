"""Server-Sent Events (SSE) service for real-time notifications.

This module provides the SSEService class for real-time event streaming
to connected clients using Server-Sent Events protocol.

**Key Components:**
* `SSEService`: Main service class for SSE operations;
* `get_sse_service`: FastAPI dependency injection factory.

**Dependencies:**
* `sse_manager`: Global SSE connection manager for user connections;
* `asyncio`: For async queue operations.

**Usage Example:**
    ```python
    from app.service.sse import get_sse_service

    @router.get("/events")
    async def events(
        user_id: int,
        sse_svc: SSEService = Depends(get_sse_service)
    ):
        return sse_svc.event_generator(user_id)
    ```

**Notes:**
- Maintains persistent connections to clients;
- Sends heartbeat every 30 seconds;
- Supports notification and level_up events;
- Uses global sse_manager for connection management.
"""

import asyncio
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from typing import Any

from app.core.config import sse_settings
from app.core.log import logging
from app.core.sse import sse_manager

logger = logging.get_logger(__name__)


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
                Type: int

        Returns:
            asyncio.Queue[str]: Queue for receiving SSE events for this user

        Example:
            ```python
            queue = await sse_svc.connect(user_id=123)
            ```
        """
        queue = await sse_manager.connect(user_id)

        logger.info(
            "User connected to SSE: user_id={user_id}",
            user_id=user_id,
        )

        return queue

    async def disconnect(self, user_id: int) -> None:
        """Disconnect user from SSE event stream.

        Args:
            user_id: ID of user to disconnect from SSE
                Type: int

        Example:
            ```python
            await sse_svc.disconnect(user_id=123)
            ```
        """
        await sse_manager.disconnect(user_id)

        logger.info(
            "User disconnected from SSE: user_id={user_id}",
            user_id=user_id,
        )

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
                Type: int
            event_type: Type of event (typically "notification" or "level_up")
                Type: str
            data: Notification data to send
                Type: dict[str, Any]

        Returns:
            None

        Example:
            ```python
            await sse_svc.send_notification(
                user_id=123,
                event_type="notification",
                data={"title": "New message", "body": "Hello!"}
            )
            ```
        """
        await sse_manager.publish(
            user_id=user_id,
            event_type="notification",
            data=data,
        )

        logger.info(
            "SSE notification sent: user_id={user_id}, event_type={event_type}",
            user_id=user_id,
            event_type=event_type,
        )


def get_sse_service() -> SSEService:
    """Create SSEService instance.

    Returns:
        SSEService: Initialized SSE service instance
    """
    return SSEService()
