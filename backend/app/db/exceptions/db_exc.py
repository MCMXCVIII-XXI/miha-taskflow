from typing import Any

from fastapi import status


class BaseDBError(Exception):
    """Base database error."""

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


class DBConnectionError(BaseDBError):
    """Database connection error."""

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


class DBRuntimeError(BaseDBError):
    """Database runtime error."""

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
