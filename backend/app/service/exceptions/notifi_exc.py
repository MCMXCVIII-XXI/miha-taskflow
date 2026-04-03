from typing import Any

from fastapi import status


class BaseNotificationError(Exception):
    """Base exception for notification errors."""

    def __init__(
        self,
        message: str,
        code: int,
        headers: dict[str, str] | None = None,
        details: dict[str, Any] | None = None,
    ):
        self.message = message
        self.code = code
        self.headers = headers
        self.details = details

    def __str__(self) -> str:
        return self.message


class NotificationNotFoundError(BaseNotificationError):
    """Exception raised when a notification is not found."""

    def __init__(
        self,
        message: str,
        headers: dict[str, str] | None = None,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            message=message,
            code=status.HTTP_404_NOT_FOUND,
            headers=headers,
            details=details,
        )


class NotificationNotActionableError(BaseNotificationError):
    """Exception raised when a notification cannot be responded to."""

    def __init__(
        self,
        message: str,
        headers: dict[str, str] | None = None,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            message=message,
            code=status.HTTP_400_BAD_REQUEST,
            headers=headers,
            details=details,
        )
