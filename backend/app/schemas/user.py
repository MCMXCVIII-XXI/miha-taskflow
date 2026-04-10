import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, SecretStr, field_validator

from app.schemas.enum import TaskSphere

from .enum import GlobalUserRole


class UserRead(BaseModel):
    """Represents a user's profile information in API responses."""

    id: int = Field(description="Unique user identifier")
    username: str = Field(description="User's unique username")
    email: str = Field(description="User's email address")
    first_name: str = Field(description="User's first name")
    last_name: str = Field(description="User's last name")
    patronymic: str | None = Field(None, description="User's patronymic (optional)")
    role: GlobalUserRole = Field(description="User's global role (USER or ADMIN)")
    is_active: bool = Field(description="User account status (active/inactive)")
    created_at: datetime = Field(description="Account creation timestamp")
    updated_at: datetime | None = Field(
        None, description="Last profile update timestamp"
    )
    admin_group_ids: list[int] = Field(
        default_factory=list, description="List of group IDs where user is admin"
    )
    member_group_ids: list[int] = Field(
        default_factory=list, description="List of group IDs where user is member"
    )

    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    """Schema for user registration and creation."""

    username: str = Field(
        description="Unique username (3-50 chars, alphanumeric with _-.)"
    )
    email: EmailStr = Field(description="Valid email address for account")
    first_name: str = Field(
        min_length=1, max_length=50, description="User's first name (1-50 chars)"
    )
    last_name: str = Field(
        min_length=1, max_length=50, description="User's last name (1-50 chars)"
    )
    patronymic: str | None = Field(None, description="User's patronymic (optional)")
    hashed_password: SecretStr = Field(
        description="User password (use 'password' field)", alias="password"
    )

    @field_validator("username", mode="before")
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Validate username format and constraints."""
        if len(v) < 3 or len(v) > 50:
            raise ValueError("Username must be between 3 and 50 characters")
        if not re.fullmatch(r"^[A-Za-z0-9][A-Za-z0-9_\-.]*[A-Za-z0-9]$", v):
            raise ValueError(
                "Username can only contain letters, digits, _, -, . \
                    and cannot start/end with special chars"
            )
        return v

    @field_validator("hashed_password", mode="before")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password format and constraints."""
        if len(v) < 8:
            raise ValueError("Password must be 8+ chars")
        if not re.search(r"(?=.*[a-z])(?=.*[A-Z])", v):
            raise ValueError("Password: 1 lowercase + 1 uppercase")
        return v


class UserUpdate(BaseModel):
    """Schema for updating user profile information."""

    username: str | None = Field(None, description="New username (must be unique)")
    email: EmailStr | None = Field(
        None, description="New email address (must be unique)"
    )
    first_name: str | None = Field(None, description="Updated first name")
    last_name: str | None = Field(None, description="Updated last name")
    patronymic: str | None = Field(None, description="Updated patronymic")


class UserSkillRead(BaseModel):
    """Schema for reading user skill and XP information."""

    id: int = Field(description="Unique skill record identifier")
    user_id: int = Field(description="ID of the user this skill belongs to")
    sphere: TaskSphere = Field(
        description="Skill sphere (BACKEND, FRONTEND, DEVOPS, QA, PRODUCT)"
    )
    xp_total: int = Field(description="Total experience points earned in this sphere")
    level: int = Field(description="Current level in this sphere")
    streak: int = Field(description="Consecutive days of activity")
    is_frozen: bool = Field(description="Whether skill progress is frozen")


class UserSkillWithTitle(UserSkillRead):
    """Schema for reading user skill with additional display information."""

    title: str = Field(description="Human-readable skill title")
    xp_to_next_level: int = Field(description="XP points needed to reach next level")
    progress_percent: int = Field(
        description="Progress percentage to next level (0-100)"
    )
