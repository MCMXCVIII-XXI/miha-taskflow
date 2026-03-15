from typing import Any

from fastapi import status


class BaseUserError(Exception):
    """Base user error."""

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


class UserUsernameConflict(BaseUserError):
    """Username already exists."""

    def __init__(
        self,
        headers: dict[str, str] | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            code=status.HTTP_409_CONFLICT,
            message="Username already exists",
            headers=headers,
            details=details,
        )


class UserEmailConflict(BaseUserError):
    """Email already exists."""

    def __init__(
        self,
        headers: dict[str, str] | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            code=status.HTTP_409_CONFLICT,
            message="Email already exists",
            headers=headers,
            details=details,
        )


class UserNotFound(BaseUserError):
    """User not found."""

    def __init__(
        self,
        headers: dict[str, str] | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            code=status.HTTP_404_NOT_FOUND,
            message="User not found",
            headers=headers,
            details=details,
        )
