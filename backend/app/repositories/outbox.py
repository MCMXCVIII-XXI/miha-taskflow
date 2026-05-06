from collections.abc import Sequence
from typing import Any

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Outbox
from app.schemas.enum import OutboxEventType, OutboxStatus


class OutboxRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    def _build_query(
        self,
        query: Select[tuple[Outbox]] = select(Outbox),
        id: int | None = None,
        event_type: OutboxEventType | None = None,
        entity_type: str | None = None,
        entity_id: int | None = None,
        payload: dict[str, Any] | None = None,
        retry_count: int | None = None,
        status: OutboxStatus | None = None,
        error: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        order_by: str | None = None,
    ) -> Select[tuple[Outbox]]:
        if id is not None:
            query = query.where(Outbox.id == id)
        if event_type is not None:
            query = query.where(Outbox.event_type == event_type)
        if entity_type is not None:
            query = query.where(Outbox.entity_type == entity_type)
        if entity_id is not None:
            query = query.where(Outbox.entity_id == entity_id)
        if payload is not None:
            query = query.where(Outbox.payload == payload)
        if retry_count is not None:
            query = query.where(Outbox.retry_count == retry_count)
        if status is not None:
            query = query.where(Outbox.status == status)
        if error is not None:
            query = query.where(Outbox.error == error)
        if order_by is not None:
            query = query.order_by(order_by)
        if limit is not None:
            query = query.limit(limit)
        if offset is not None:
            query = query.offset(offset)
        return query

    async def get(
        self,
        id: int | None = None,
        event_type: OutboxEventType | None = None,
        entity_type: str | None = None,
        entity_id: int | None = None,
        payload: dict[str, Any] | None = None,
        retry_count: int | None = None,
        status: OutboxStatus | None = None,
        error: str | None = None,
        order_by: str | None = None,
    ) -> Outbox | None:
        query = self._build_query(
            id=id,
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            payload=payload,
            retry_count=retry_count,
            status=status,
            error=error,
            order_by=order_by,
        )
        return await self._db.scalar(query)

    async def find_many(
        self,
        event_type: OutboxEventType | None = None,
        entity_type: str | None = None,
        entity_id: int | None = None,
        payload: dict[str, Any] | None = None,
        retry_count: int | None = None,
        status: OutboxStatus | None = None,
        error: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        order_by: Any | None = None,
    ) -> Sequence[Outbox]:
        query = self._build_query(
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            payload=payload,
            retry_count=retry_count,
            status=status,
            error=error,
            limit=limit,
            offset=offset,
            order_by=order_by,
        )
        result = await self._db.scalars(query)
        return result.all()

    async def find_failed(
        self,
        max_retries: int,
        order_by: Any | None = None,
        limit: int | None = None,
    ) -> list[Outbox]:
        query = select(Outbox).where(
            Outbox.retry_count < max_retries,
        )
        query = self._build_query(
            query=query,
            status=OutboxStatus.FAILED,
            order_by=order_by,
            limit=limit,
        )
        result = await self._db.scalars(query)
        return list(result.all())

    async def add(
        self,
        event_type: OutboxEventType,
        entity_type: str,
        entity_id: int,
        payload: dict[str, Any] | None = None,
        status: OutboxStatus = OutboxStatus.PENDING,
    ) -> Outbox:
        outbox = Outbox(
            event_type=event_type,
            entity_id=entity_id,
            entity_type=entity_type,
            payload=payload,
            status=status,
        )
        self._db.add(outbox)
        await self._db.flush()
        return outbox

    async def mark_processed(self, outbox_id: int) -> None:
        outbox = await self.get(id=outbox_id)
        if outbox:
            outbox.status = OutboxStatus.PROCESSING
            await self._db.commit()

    async def increment_retry(self, outbox_id: int) -> Outbox | None:
        outbox = await self.get(id=outbox_id)
        if outbox:
            outbox.retry_count += 1
            await self._db.flush()
        return outbox
