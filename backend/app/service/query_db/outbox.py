from typing import Any

from sqlalchemy import Select, select

from app.models import (
    Outbox,
)
from app.schemas.enum import OutboxEventType, OutboxStatus


class OutboxQueries:
    @staticmethod
    def get_outbox(
        id: int | None = None,
        event_type: OutboxEventType | None = None,
        entity_type: str | None = None,
        entity_id: int | None = None,
        payload: dict[str, Any] | None = None,
        retry_count: int | None = None,
        status: OutboxStatus | None = None,
        error: str | None = None,
    ) -> Select[tuple[Outbox]]:
        base = select(Outbox)
        if id is not None:
            base = base.where(Outbox.id == id)
        if event_type is not None:
            base = base.where(Outbox.event_type == event_type)
        if entity_type is not None:
            base = base.where(Outbox.entity_type == entity_type)
        if entity_id is not None:
            base = base.where(Outbox.entity_id == entity_id)
        if payload is not None:
            base = base.where(Outbox.payload == payload)
        if retry_count is not None:
            base = base.where(Outbox.retry_count == retry_count)
        if status is not None:
            base = base.where(Outbox.status == status)
        if error is not None:
            base = base.where(Outbox.error == error)
        return base
