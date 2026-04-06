from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from .enum import (
    GlobalUserRole,
    NotificationResponse,
    NotificationStatus,
    NotificationTargetType,
    NotificationType,
    TaskPriority,
    TaskStatus,
)


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


###############################################################################
# USER ########################################################################


class UserSearch(BaseModel):
    """Schema for searching users."""

    id: int | None = Field(None, description="Sort by user ID")
    username: str | None = Field(None, min_length=3, description="Sort by username")
    email: EmailStr | None = Field(None, description="Sort by email")
    first_name: str | None = Field(None, min_length=2, description="Sort by first name")
    last_name: str | None = Field(None, min_length=2, description="Sort by last name")
    patronymic: str | None = Field(None, min_length=2, description="Sort by patronymic")
    role: GlobalUserRole | None = Field(None, description="Sort by user role")
    created_at: datetime | None = Field(None, description="Sort by creation date")

    model_config = ConfigDict(
        extra="forbid",
    )


###############################################################################
# USER GROUP ##################################################################


class UserGroupSearch(BaseModel):
    """Schema for searching user groups."""

    id: int | None = Field(None, description="Sort by group ID")
    name: str | None = Field(None, max_length=50, description="Sort by group name")
    created_at: datetime | None = Field(None, description="Sort by creation date")

    model_config = ConfigDict(extra="forbid")


###############################################################################
# NOTIFICATION ################################################################


class NotificationSearch(BaseModel):
    """Schema for searching notifications."""

    id: int | None = Field(None, description="Notification ID")
    sender_id: int | None = Field(None, description="Sender user ID")
    recipient_id: int | None = Field(None, description="Recipient user ID")
    type: NotificationType | None = Field(None, description="Notification type")
    title: str | None = Field(None, description="Notification title")
    message: str | None = Field(None, description="Notification message")
    target_id: int | None = Field(None, description="Target ID")
    target_type: NotificationTargetType | None = Field(None, description="Target type")
    response: NotificationResponse | None = Field(
        None, description="Notification response"
    )
    status: NotificationStatus | None = Field(None, description="Notification status")
    created_at: datetime | None = Field(None, description="Created at")

    model_config = ConfigDict(extra="forbid")
