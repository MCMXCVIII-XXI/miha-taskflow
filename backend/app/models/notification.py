from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.db.mixins import IdPkMixin
from app.schemas import (
    NotificationResponse,
    NotificationStatus,
    NotificationTargetType,
    NotificationType,
)

if TYPE_CHECKING:
    from app.models.user import User


class Notification(Base, IdPkMixin):
    sender_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    recipient_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    type: Mapped[NotificationType] = mapped_column(Enum(NotificationType), index=True)
    title: Mapped[str] = mapped_column(String(255), index=True)
    message: Mapped[str] = mapped_column(String(255))
    target_id: Mapped[int] = mapped_column()
    target_type: Mapped[NotificationTargetType] = mapped_column(
        Enum(NotificationTargetType), index=True
    )
    sender: Mapped["User"] = relationship(
        "User",
        back_populates="notifications_sent",
        foreign_keys="Notification.sender_id",
    )
    recipient: Mapped["User"] = relationship(
        "User",
        back_populates="notifications_received",
        foreign_keys="Notification.recipient_id",
    )
    response: Mapped[NotificationResponse] = mapped_column(
        Enum(NotificationResponse), default=NotificationResponse.WAITING, index=True
    )
    status: Mapped[NotificationStatus] = mapped_column(
        Enum(NotificationStatus), default=NotificationStatus.UNREAD, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
