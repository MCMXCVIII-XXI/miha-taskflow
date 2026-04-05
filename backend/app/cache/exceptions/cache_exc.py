from typing import Any

from fastapi import status


class BaseCacheError(Exception):
    """Base cache errors."""

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


class CacheConnectionError(BaseCacheError):
    """Cache connection error."""

    def __init__(
        self,
        message: str,
        headers: dict[str, str] | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            code=status.HTTP_503_SERVICE_UNAVAILABLE,
            message=message,
            headers=headers,
            details=details,
        )


class CacheNotFoundError(BaseCacheError):
    """Cache not found error."""

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
