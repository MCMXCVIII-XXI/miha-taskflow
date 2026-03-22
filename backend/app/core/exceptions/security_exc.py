from typing import Any

from fastapi import status


class BaseSecurityError(Exception):
    """Base security error."""

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


class SecurityCouldNotVerify(BaseSecurityError):
    """Could not verify credentials."""

    def __init__(
        self,
        message: str,
        headers: dict[str, str] | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            code=status.HTTP_401_UNAUTHORIZED,
            message=message,
            headers=headers,
            details=details,
        )


class SecurityRefreshTokenError(BaseSecurityError):
    """Could not validate refresh token."""

    def __init__(
        self,
        message: str,
        headers: dict[str, str] | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            code=status.HTTP_401_UNAUTHORIZED,
            message=message,
            headers=headers,
            details=details,
        )


class SecurityAccessTokenError(BaseSecurityError):
    """Could not validate access token."""

    def __init__(
        self,
        message: str,
        headers: dict[str, str] | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            code=status.HTTP_401_UNAUTHORIZED,
            message=message,
            headers=headers,
            details=details,
        )


class SecurityExpired(BaseSecurityError):
    """Token has expired."""

    def __init__(
        self,
        message: str,
        headers: dict[str, str] | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            code=status.HTTP_401_UNAUTHORIZED,
            message=message,
            headers=headers,
            details=details,
        )


class SecurityNotAuthorized(BaseSecurityError):
    """You cannot perform this action."""

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


class SecurityPermissionDenied(BaseSecurityError):
    """You do not have permission to perform this action."""

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
