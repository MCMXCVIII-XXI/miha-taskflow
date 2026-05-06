from typing import Any

from fastapi import status


class BaseGroupError(Exception):
    """Base group error."""

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


class GroupNameConflict(BaseGroupError):
    """Name already exists."""

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


class GroupNotFound(BaseGroupError):
    """Group not found."""

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


class ForbiddenGroupAccess(BaseGroupError):
    """Forbidden group access."""

    def __init__(
        self,
        message: str,
        headers: dict[str, str] | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            code=status.HTTP_403_FORBIDDEN,
            message=message,
            headers=headers,
            details=details,
        )


class MemberAlreadyExists(BaseGroupError):
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


class MemberNotFound(BaseGroupError):
    """Member not found."""

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


class MemberNotAdmin(BaseGroupError):
    """Member is not an admin."""

    def __init__(
        self,
        message: str,
        headers: dict[str, str] | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            code=status.HTTP_403_FORBIDDEN,
            message=message,
            headers=headers,
            details=details,
        )


class JoinRequestNotFound(BaseGroupError):
    """Join request not found."""

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


class JoinRequestAlreadyExists(BaseGroupError):
    """Join request already exists."""

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


class JoinRequestAlreadyHandled(BaseGroupError):
    """Join request already handled."""

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


class GroupMissingContextIdError(BaseGroupError):
    """Group missing context id."""

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


class GroupRuntimeError(BaseGroupError):
    """Group runtime error."""

    def __init__(
        self,
        message: str,
        headers: dict[str, str] | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=message,
            headers=headers,
            details=details,
        )
