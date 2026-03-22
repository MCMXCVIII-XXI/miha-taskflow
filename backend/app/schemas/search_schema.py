from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from .task_schemas import TaskPriority, TaskStatus
from .user_schemas import UserRole


###############################################################################
# TASK ########################################################################
class TaskSearch(BaseModel):
    """Schema for searching tasks."""

    id: int | None = Field(None, description="Sort by task ID")
    title: str | None = Field(None, description="Sort by task title")
    status: TaskStatus | None = Field(None, description="Sort by task status")
    priority: TaskPriority | None = Field(None, description="Sort by task priority")
    created_at: datetime | None = Field(None, description="Sort by task creation date")

    model_config = ConfigDict(
        extra="forbid",
    )


class TaskSort(BaseModel):
    """Schema for sorting tasks."""

    id: int | None = Field(None, description="Sort by task ID")
    title: str | None = Field(None, description="Sort by task title")
    status: TaskStatus | None = Field(None, description="Sort by task status")
    priority: TaskPriority | None = Field(None, description="Sort by task priority")
    is_active: bool | None = Field(None, description="Sort by task active status")
    created_at: datetime | None = Field(None, description="Sort by task creation date")

    model_config = ConfigDict(
        extra="forbid",
    )


###############################################################################
# USER #########################################################################


class UserSearch(BaseModel):
    """Schema for searching users."""

    id: int | None = Field(None, description="Sort by user ID")
    username: str | None = Field(None, min_length=3, description="Sort by username")
    email: EmailStr | None = Field(None, description="Sort by email")
    first_name: str | None = Field(None, min_length=2, description="Sort by first name")
    last_name: str | None = Field(None, min_length=2, description="Sort by last name")
    patronymic: str | None = Field(None, min_length=2, description="Sort by patronymic")
    role: UserRole | None = Field(None, description="Sort by user role")
    created_at: datetime | None = Field(None, description="Sort by creation date")

    model_config = ConfigDict(
        extra="forbid",
    )


class UserSort(BaseModel):
    """Schema for sorting users."""

    id: int | None = Field(None, description="Sort by user ID")
    username: str | None = Field(None, description="Sort by username")
    email: EmailStr | None = Field(None, description="Sort by email")
    first_name: str | None = Field(None, description="Sort by first name")
    last_name: str | None = Field(None, description="Sort by last name")
    patronymic: str | None = Field(None, description="Sort by patronymic")
    role: UserRole | None = Field(None, description="Sort by user role")
    created_at: datetime | None = Field(None, description="Sort by creation date")

    model_config = ConfigDict(
        extra="forbid",
    )


###############################################################################
# USER GROUP ###################################################################


class UserGroupSearch(BaseModel):
    """Schema for searching user groups."""

    id: int | None = Field(None, description="Sort by group ID")
    name: str | None = Field(None, max_length=50, description="Sort by group name")
    created_at: datetime | None = Field(None, description="Sort by creation date")

    model_config = ConfigDict(extra="forbid")


class UserGroupSort(BaseModel):
    """Schema for sorting user groups."""

    id: int | None = Field(None, description="Sort by group ID")
    name: str | None = Field(None, description="Sort by group name")
    created_at: datetime | None = Field(None, description="Sort by creation date")

    model_config = ConfigDict(extra="forbid")


###############################################################################
###############################################################################
