from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class GroupVisibility(Enum):
    PUBLIC = "public"
    PRIVATE = "private"


class InvitePolicy(Enum):
    ADMIN_ONLY = "admin_only"
    ALL_MEMBERS = "all_members"


class UserGroupRead(BaseModel):
    """UserGroup API response."""

    id: int = Field(description="Group ID")
    name: str = Field(max_length=50, description="Group name")
    description: str | None = Field(default=None, description="Group description")
    admin_id: int = Field(description="Admin ID")
    visibility: GroupVisibility = Field(
        GroupVisibility.PUBLIC, description="Group visibility"
    )
    is_active: bool = Field(description="Group is active")
    invite_policy: InvitePolicy = Field(
        InvitePolicy.ADMIN_ONLY, description="Invite policy"
    )
    created_at: datetime = Field(description="Group creation date")
    updated_at: datetime | None = Field(default=None, description="Group update date")

    model_config = ConfigDict(from_attributes=True)


class UserGroupCreate(BaseModel):
    """Schema for creating user groups."""

    name: str = Field(max_length=50, description="Group name")
    description: str | None = Field(default=None, description="Group description")
    visibility: GroupVisibility = Field(
        default=GroupVisibility.PUBLIC, description="Group visibility"
    )
    parent_group_id: int | None = Field(
        default=None, description="Parent group ID for subgroups"
    )
    invite_policy: InvitePolicy = Field(
        default=InvitePolicy.ADMIN_ONLY, description="Invite policy"
    )

    @field_validator("parent_group_id", mode="before")
    @classmethod
    def convert_zero_to_none(cls, value):
        if value == 0:
            return None
        return value


class UserGroupUpdate(BaseModel):
    """Schema for updating user groups."""

    name: str | None = Field(None, max_length=50, description="Group name")
    description: str | None = Field(
        None, max_length=255, description="Group description"
    )
    visibility: GroupVisibility | None = Field(None, description="Group visibility")
    invite_policy: InvitePolicy | None = Field(None, description="Invite policy")


class UserGroupMembership(BaseModel):
    """Schema for user group membership."""

    id: int = Field(description="User group membership ID")
    user_id: int = Field(description="User ID")
    group_id: int = Field(description="Group ID")
    created_at: datetime = Field(description="User group membership creation date")
    updated_at: datetime | None = Field(
        default=None, description="User group membership update date"
    )

    model_config = ConfigDict(from_attributes=True)


class UserGroupMembershipCreate(BaseModel):
    """Schema for creating user group membership."""

    user_id: int = Field(description="User ID")
    group_id: int = Field(description="Group ID")
