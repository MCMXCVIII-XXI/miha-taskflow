from typing import Any

from fastapi import status


class BaseJoinRequestError(Exception):
    """Base exception for join request errors."""

    def __init__(
        self,
        code: int,
        message: str,
        headers: dict[str, str] | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.code = code
        self.message = message
        self.headers = headers
        self.details = details

    def __str__(self) -> str:
        return self.message


class JoinRequestNotFound(BaseJoinRequestError):
    """Raised when a join request is not found."""

    def __init__(
        self,
        message: str,
        headers: dict[str, str] | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            code=status.HTTP_404_NOT_FOUND,
            message=message,
            headers=headers,
            details=details,
        )


class JoinRequestAlreadyExists(BaseJoinRequestError):
    """Raised when a join request already exists."""

    def __init__(
        self,
        message: str,
        headers: dict[str, str] | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            code=status.HTTP_409_CONFLICT,
            message=message,
            headers=headers,
            details=details,
        )


class JoinRequestAlreadyHandled(BaseJoinRequestError):
    """Raised when a join request already handled."""

    def __init__(
        self,
        message: str,
        headers: dict[str, str] | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            code=status.HTTP_400_BAD_REQUEST,
            message=message,
            headers=headers,
            details=details,
        )
