import re
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, EmailStr, Field, SecretStr, field_validator


class UserRole(Enum):
    USER = "user"
    MEMBER = "member"
    GROUP_ADMIN = "group_admin"
    TASK_LEADER = "task_leader"
    ADMIN = "admin"


class UserRead(BaseModel):
    """User API response."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="User ID")
    username: str = Field(description="User username")
    email: str = Field(description="User email")
    first_name: str = Field(description="First name")
    last_name: str = Field(description="Last name")
    patronymic: str | None = Field(None, description="Patronymic")
    role: UserRole = Field(description="User role")
    is_active: bool = Field(description="User is active")
    created_at: datetime = Field(description="User creation date")
    updated_at: datetime | None = Field(None, description="User update date")
    admin_group_ids: list[int] = Field(default_factory=list, description="Admin groups")
    member_group_ids: list[int] = Field(
        default_factory=list, description="Member groups"
    )

    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    """Schema for creating users."""

    username: str = Field(description="User username")
    email: EmailStr = Field(description="User email")
    first_name: str = Field(min_length=1, max_length=50, description="First name")
    last_name: str = Field(min_length=1, max_length=50, description="Last name")
    patronymic: str | None = Field(None, description="Patronymic")
    hashed_password: SecretStr = Field(description="User password", alias="password")

    @field_validator("username", mode="before")
    @classmethod
    def validate_username(cls, v: str) -> str:
        if len(v) < 3 or len(v) > 50:
            raise ValueError("Username: 3-50 chars (no spaces)")
        if not re.fullmatch(r"^[A-Za-z0-9][A-Za-z0-9_\-.]*[A-Za-z0-9]$", v):
            raise ValueError("Username: letters, digits, _, -, . (no start/end)")
        return v

    @field_validator("hashed_password", mode="before")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be 8+ chars")
        if not re.search(r"(?=.*[a-z])(?=.*[A-Z])", v):
            raise ValueError("Password: 1 lowercase + 1 uppercase")
        return v


class UserUpdate(BaseModel):
    """Schema for updating user profile."""

    username: str | None = Field(None, description="User username")
    email: EmailStr | None = Field(None, description="User email")
    first_name: str | None = Field(None, description="First name")
    last_name: str | None = Field(None, description="Last name")
    patronymic: str | None = Field(None, description="Patronymic")
