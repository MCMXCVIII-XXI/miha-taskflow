"""Auth endpoint examples for Swagger documentation."""

from typing import Any, ClassVar


class AuthExamples:
    """Examples for authentication endpoints."""

    REGISTER_SUCCESS: ClassVar[dict[str, Any]] = {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "token_type": "bearer",
        "expires_in": 30,
    }

    LOGIN_SUCCESS: ClassVar[dict[str, Any]] = {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "token_type": "bearer",
        "expires_in": 30,
    }

    REFRESH_SUCCESS: ClassVar[dict[str, Any]] = {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "token_type": "bearer",
        "expires_in": 30,
    }

    REFRESH_TOKEN_SUCCESS: ClassVar[dict[str, Any]] = {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "token_type": "bearer",
        "expires_in": 30,
    }

    LOGOUT_SUCCESS: ClassVar[dict[str, Any]] = {"message": "Logged out successfully"}

    REGISTER_REQUEST: ClassVar[dict[str, Any]] = {
        "username": "new_user",
        "email": "new@example.com",
        "password": "SecurePass123",
        "first_name": "New",
        "last_name": "User",
    }

    LOGIN_REQUEST: ClassVar[dict[str, Any]] = {
        "username": "new_user",
        "password": "SecurePass123",
    }

    REFRESH_REQUEST: ClassVar[dict[str, Any]] = {
        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    }

    DUPLICATE_EMAIL: ClassVar[dict[str, Any]] = {
        "detail": "User with this email already exists"
    }

    DUPLICATE_USERNAME: ClassVar[dict[str, Any]] = {
        "detail": "User with this username already exists"
    }

    INVALID_CREDENTIALS: ClassVar[dict[str, Any]] = {
        "detail": "Incorrect username or password"
    }

    INVALID_TOKEN: ClassVar[dict[str, Any]] = {"detail": "Invalid or expired token"}

    VALIDATION_ERROR: ClassVar[dict[str, Any]] = {
        "detail": [
            {
                "loc": ["body", "email"],
                "msg": "value is not a valid email address",
                "type": "value_error.email",
            }
        ]
    }
