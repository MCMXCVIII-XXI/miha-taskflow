from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UserGroupBase(BaseModel):
    name: str = Field(max_length=50, description="Group name")


class UserGroupCreate(UserGroupBase):
    pass


class UserGroup(UserGroupBase):
    id: int
    admin_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class UserGroupMembershipBase(BaseModel):
    user_id: int
    group_id: int


class UserGroupMembershipCreate(UserGroupMembershipBase):
    pass


class UserGroupMembership(UserGroupMembershipBase):
    id: int
    created_at: datetime
    updated_at: datetime | None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
