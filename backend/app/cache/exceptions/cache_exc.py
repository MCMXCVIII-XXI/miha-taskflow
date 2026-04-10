"""Cache exception classes for error handling.

This module defines custom exception classes for various cache-related errors
that can occur during application operation. Each exception includes
appropriate HTTP status codes and structured error information.

Exceptions:
    BaseCacheError: Base class for all cache exceptions
    CacheConnectionError: Raised when cache connection fails
    CacheNotFoundError: Raised when cached item is not found
"""

from typing import Any

from fastapi import status


class BaseCacheError(Exception):
    """Base class for all cache-related exceptions.

    Provides common structure for cache exceptions with HTTP status codes,
    error messages, headers, and detailed information.

    Attributes:
        code (int): HTTP status code for the error
        message (str): Human-readable error description
        headers (dict[str, str], optional): HTTP headers to include in response
        details (dict[str, Any], optional): Additional error details
    """

    def __init__(
        self,
        code: int,
        message: str,
        headers: dict[str, str] | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize base cache exception.

        Args:
            code (int): HTTP status code
            message (str): Error description
            headers (dict[str, str], optional): HTTP response headers
            details (dict[str, Any], optional): Additional error details
        """
        self.code = code
        self.message = message
        self.headers = headers
        self.details = details

    def __str__(self) -> str:
        """String representation of the exception."""
        return self.message


class CacheConnectionError(BaseCacheError):
    """Exception raised when cache connection fails.

    This exception is raised when the application cannot establish
    or maintain a connection to the cache backend (e.g., Redis).

    HTTP Status: 503 SERVICE UNAVAILABLE
    """

    def __init__(
        self,
        message: str,
        headers: dict[str, str] | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize cache connection error.

        Args:
            message (str): Connection error description
            headers (dict[str, str], optional): HTTP response headers
            details (dict[str, Any], optional): Additional error details
        """
        super().__init__(
            code=status.HTTP_503_SERVICE_UNAVAILABLE,
            message=message,
            headers=headers,
            details=details,
        )


class CacheNotFoundError(BaseCacheError):
    """Exception raised when cached item is not found.

    This exception is raised when attempting to access a cache item
    that does not exist or has expired.

    HTTP Status: 404 NOT FOUND
    """

    def __init__(
        self,
        message: str,
        headers: dict[str, str] | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize cache not found error.

        Args:
            message (str): Not found error description
            headers (dict[str, str], optional): HTTP response headers
            details (dict[str, Any], optional): Additional error details
        """
        super().__init__(
            code=status.HTTP_404_NOT_FOUND,
            message=message,
            headers=headers,
            details=details,
        )
