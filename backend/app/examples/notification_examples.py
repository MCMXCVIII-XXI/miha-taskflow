"""Notification endpoint examples for Swagger documentation."""

from typing import Any, ClassVar


class NotificationExamples:
    """Examples for notification endpoints."""

    GET_ALL: ClassVar[dict[str, Any]] = {
        "notifications": [
            {
                "id": 1,
                "message": "You were invited to a task",
                "type": "TASK_INVITE",
                "is_read": False,
                "user_id": 1,
                "created_at": "2024-01-15T10:30:00Z",
            }
        ],
        "total": 1,
    }

    UNREAD_COUNT: ClassVar[dict[str, Any]] = {"count": 5}

    MARK_READ_SUCCESS: ClassVar[dict[str, Any]] = {"id": 1, "is_read": True}

    MARK_ALL_READ_SUCCESS: ClassVar[dict[str, Any]] = {"updated": 5}

    NOT_FOUND: ClassVar[dict[str, Any]] = {"detail": "Notification not found"}


class SSEExamples:
    """Examples for SSE notification endpoint."""

    SSE_CONNECTED: ClassVar[dict[str, Any]] = {
        "event": "connected",
        "data": {"message": "Connected to SSE stream"},
    }

    SSE_NOTIFICATION: ClassVar[dict[str, Any]] = {
        "event": "notification",
        "data": {
            "id": 1,
            "message": "New notification",
            "type": "TASK_INVITE",
        },
    }
