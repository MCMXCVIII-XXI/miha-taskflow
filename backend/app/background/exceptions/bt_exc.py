from typing import Any

from fastapi import status


class BaseBackgroundError(Exception):
    def __init__(
        self,
        message: str,
        headers: dict[str, str] | None = None,
        details: dict[str, Any] | None = None,
        code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
    ) -> None:
        self.code = code
        self.message = message
        self.headers = headers
        self.details = details

    def __str__(self) -> str:
        return self.message


class BackgroundBrokerUrlError(BaseBackgroundError):
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


class BackgroundBackendUrlError(BaseBackgroundError):
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


class BackgroundAsyncTimeoutError(BaseBackgroundError):
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


class BackgroundRuntimeError(BaseBackgroundError):
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
