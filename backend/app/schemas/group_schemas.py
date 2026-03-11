from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UserGroup(BaseModel):
    id: int = Field(description="Group ID")
    name: str = Field(max_length=50, description="Group name")
    admin_id: int = Field(description="Admin ID")
    is_active: bool = Field(description="Group is active")
    created_at: datetime = Field(description="Group creation date")
    updated_at: datetime | None = Field(default=None, description="Group update date")

    model_config = ConfigDict(from_attributes=True)


class UserGroupCreate(BaseModel):
    name: str = Field(max_length=50, description="Group name")


class UserGroupUpdate(BaseModel):
    name: str = Field(max_length=50, description="Group name")


class UserGroupMembership(BaseModel):
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
    user_id: int = Field(description="User ID")
    group_id: int = Field(description="Group ID")
