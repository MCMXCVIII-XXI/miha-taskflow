from typing import Any

from fastapi import status


class BaseGroupMembershipError(Exception):
    """Base group membership error."""

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


class GroupMembershipMemberConflict(BaseGroupMembershipError):
    """Member already exists."""

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


class GroupMembershipNotFound(BaseGroupMembershipError):
    """Group membership not found."""

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
