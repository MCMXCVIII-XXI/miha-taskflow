from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from .enum import (
    NotificationResponse,
    NotificationStatus,
    NotificationTargetType,
    NotificationType,
)


class NotificationRead(BaseModel):
    id: int = Field(description="Notification ID")
    sender_id: int = Field(description="Sender user ID")
    recipient_id: int = Field(description="Recipient user ID")
    type: NotificationType = Field(description="Notification type")
    title: str = Field(description="Notification title")
    message: str = Field(description="Notification message")
    target_id: int = Field(description="Target ID")
    target_type: NotificationTargetType = Field(description="Target type")
    response: NotificationResponse = Field(description="Notification response")
    status: NotificationStatus = Field(description="Notification status")
    created_at: datetime = Field(description="Created at")

    model_config = ConfigDict(from_attributes=True)


class NotificationCreate(BaseModel):
    recipient_id: int = Field(description="Recipient user ID")
    type: NotificationType = Field(description="Notification type")
    title: str = Field(max_length=255, description="Notification title")
    message: str = Field(max_length=255, description="Notification message")
    target_id: int = Field(description="Target ID")
    target_type: NotificationTargetType = Field(description="Target type")


class NotificationUpdate(BaseModel):
    status: NotificationStatus | None = Field(
        default=None, description="Notification status"
    )
    response: NotificationResponse | None = Field(
        default=None, description="Notification response"
    )


class NotificationRespond(BaseModel):
    response: NotificationResponse = Field(description="Accept or Refusal")
