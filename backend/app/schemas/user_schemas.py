import re
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, EmailStr, Field, SecretStr, field_validator


class UserRole(Enum):
    GUEST = "guest"
    MEMBER = "member"
    LEAD = "lead"
    MANAGER = "manager"
    ADMIN = "admin"


class UserBase(BaseModel):
    """
    User API response.
    """
    id: int = Field(description="User ID")
    username: str = Field(description="User username")
    email: str = Field(description="User email")
    role: UserRole = Field(description="User role")
    created_at: datetime = Field(description="User creation date")
    updated_at: datetime | None = Field(None, description="User update date")
    admin_group_ids: list[int] = Field(default_factory=list, description="Admin")
    member_group_ids: list[int] = Field(default_factory=list, description="Participant")

    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    """
    User registration.
    """
    username: str = Field(..., description="User username")
    email: EmailStr = Field(..., description="User email")
    password: SecretStr = Field(..., description="User password")
    
    @field_validator("username", mode="before")
    @classmethod
    def validate_username(cls, v: str) -> str:
        if len(v) < 3 or len(v) > 50:
            raise ValueError("Username: 3-50 chars")
        if not re.fullmatch(r"^[A-Za-z0-9][A-Za-z0-9_\-.]*[A-Za-z0-9]$", v):
            raise ValueError("Username: letters, digits, _, -, . (no start/end)")
        return v
    
    @field_validator("password", mode="before")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password: min 8 chars")
        if not re.search(r"(?=.*[a-z])(?=.*[A-Z])", v):
            raise ValueError("Password: 1 lowercase + 1 uppercase")
        return v


class UserUpdate(BaseModel):
    """
    Update user profile.
    """
    username: str | None = Field(None, description="User username")
    email: EmailStr | None = Field(None, description="User email")

