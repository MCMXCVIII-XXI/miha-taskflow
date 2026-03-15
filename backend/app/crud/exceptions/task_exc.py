from typing import Any

from fastapi import status


class BaseTaskError(Exception):
    """Base task error."""

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


class TaskTitleConflict(BaseTaskError):
    """Title already exists."""

    def __init__(
        self,
        headers: dict[str, str] | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            code=status.HTTP_409_CONFLICT,
            message="Title already exists",
            headers=headers,
            details=details,
        )


class TaskNotFound(BaseTaskError):
    """Task not found."""

    def __init__(
        self,
        headers: dict[str, str] | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            code=status.HTTP_404_NOT_FOUND,
            message="Title not found",
            headers=headers,
            details=details,
        )
