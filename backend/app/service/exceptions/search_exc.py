from typing import Any

from fastapi import status


class BaseSearchError(Exception):
    """Base search error."""

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


class TooManySortFieldsError(BaseSearchError):
    """Raised when too many sort fields are provided."""

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


class InvalidFieldError(BaseSearchError):
    """Raised when an invalid sort field is provided."""

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
