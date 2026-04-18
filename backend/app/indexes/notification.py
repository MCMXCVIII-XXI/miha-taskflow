from datetime import datetime
from typing import Any, ClassVar

from elasticsearch.dsl import (
    AsyncDocument,
    Date,
    Integer,
    Keyword,
    M,
    Text,
    mapped_field,
)

from app.models import Notification
from app.schemas import NotificationRead

from .utils import RUSSIAN_ANALYZER_SETTINGS, get_index_name


class NotificationDoc(AsyncDocument):
    """ES Document for Notification."""

    id: M[int] = mapped_field(Integer())
    sender_id: M[int] = mapped_field(Integer())
    recipient_id: M[int] = mapped_field(Integer())
    type: M[str] = mapped_field(Keyword())
    title: M[str] = mapped_field(Text(analyzer="notification_analyzer"))
    message: M[str] = mapped_field(Text(analyzer="notification_analyzer"))
    target_id: M[int | None] = mapped_field(Integer())
    target_type: M[str] = mapped_field(Keyword())
    response: M[str | None] = mapped_field(Keyword())
    status: M[str] = mapped_field(Keyword())
    created_at: M[datetime] = mapped_field(Date())

    class Index:
        name = get_index_name("notifications_v1")
        settings: ClassVar[dict[str, Any]] = {
            "number_of_shards": 3,
            "number_of_replicas": 1,
            "analysis": RUSSIAN_ANALYZER_SETTINGS,
            "sort": {
                "_score": "first",
                "created_at": {"order": "desc"},
            },
        }

    @classmethod
    def from_orm(cls, notification: Notification) -> "NotificationDoc":
        """SQLAlchemy Notification → ES Document."""
        return cls(
            id=notification.id,
            sender_id=int(notification.sender_id),
            recipient_id=int(notification.recipient_id),
            type=notification.type.value
            if hasattr(notification.type, "value")
            else str(notification.type.value or ""),
            title=notification.title or "",
            message=notification.message or "",
            target_id=int(notification.target_id) if notification.target_id else None,
            target_type=notification.target_type.value or "",
            response=notification.response.value or None,
            status=notification.status.value
            if hasattr(notification.status.value, "value")
            else str(notification.status.value or ""),
            created_at=notification.created_at,
        )

    def to_read_schema(self) -> NotificationRead:
        """ES → Pydantic NotificationRead."""
        return NotificationRead.model_validate(self)
