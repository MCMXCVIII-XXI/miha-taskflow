from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UserGroupRead(BaseModel):
    """UserGroup API response."""

    id: int = Field(description="Group ID")
    name: str = Field(max_length=50, description="Group name")
    description: str | None = Field(default=None, description="Group description")
    admin_id: int = Field(description="Admin ID")
    is_active: bool = Field(description="Group is active")
    created_at: datetime = Field(description="Group creation date")
    updated_at: datetime | None = Field(default=None, description="Group update date")

    model_config = ConfigDict(from_attributes=True)


class UserGroupCreate(BaseModel):
    """Schema for creating user groups."""

    name: str = Field(max_length=50, description="Group name")
    description: str | None = Field(default=None, description="Group description")
    admin_id: int = Field(description="Admin ID")


class UserGroupUpdate(BaseModel):
    """Schema for updating user groups."""

    name: str = Field(max_length=50, description="Group name")


class UserGroupMembership(BaseModel):
    """Schema for user group membership."""

    id: int = Field(description="User group membership ID")
    user_id: int = Field(description="User ID")
    group_id: int = Field(description="Group ID")
    created_at: datetime = Field(description="User group membership creation date")
    updated_at: datetime | None = Field(
        default=None, description="User group membership update date"
    )
    is_active: bool = Field(default=True, description="User group membership is active")

    model_config = ConfigDict(from_attributes=True)


class UserGroupMembershipCreate(BaseModel):
    """Schema for creating user group membership."""

    user_id: int = Field(description="User ID")
    group_id: int = Field(description="Group ID")
