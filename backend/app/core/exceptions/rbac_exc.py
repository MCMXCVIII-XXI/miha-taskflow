"""Role-Based Access Control (RBAC) exception classes for error handling.

This module defines custom exception classes for RBAC-related errors
that can occur during role and permission management operations.
Each exception includes appropriate HTTP status codes and structured error information.
"""

from typing import Any

from fastapi import status


class BaseRBACError(Exception):
    """Base class for all Role-Based Access Control exceptions.

    Provides common structure for RBAC exceptions with HTTP status codes,
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
        """Initialize base RBAC exception.

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


class RoleNotFound(BaseRBACError):
    """Exception raised when requested role is not found.

    This exception is raised when attempting to access or modify a role
    that does not exist in the system.

    HTTP Status: 404 NOT FOUND
    """

    def __init__(
        self,
        message: str,
        headers: dict[str, str] | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize role not found error.

        Args:
            message (str): Error description
            headers (dict[str, str], optional): HTTP response headers
            details (dict[str, Any], optional): Additional error details
        """
        super().__init__(
            code=status.HTTP_404_NOT_FOUND,
            message=message,
            headers=headers,
            details=details,
        )


class RoleAlreadyExistsError(BaseRBACError):
    """Exception raised when attempting to create a role that already exists.

    This exception is raised during role creation when a role with the same
    name already exists in the system.

    HTTP Status: 400 BAD REQUEST
    """

    def __init__(
        self,
        message: str,
        headers: dict[str, str] | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize role already exists error.

        Args:
            message (str): Error description
            headers (dict[str, str], optional): HTTP response headers
            details (dict[str, Any], optional): Additional error details
        """
        super().__init__(
            code=status.HTTP_400_BAD_REQUEST,
            message=message,
            headers=headers,
            details=details,
        )
