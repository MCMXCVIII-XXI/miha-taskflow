from collections.abc import Sequence

from sqlalchemy import Select, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Notification
from app.schemas.enum import (
    NotificationResponse,
    NotificationStatus,
    NotificationTargetType,
    NotificationType,
)


class NotificationRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    def _apply_pagination(
        self,
        query: Select[tuple[Notification]],
        limit: int | None = None,
        offset: int | None = None,
    ) -> Select[tuple[Notification]]:
        if limit is not None:
            query = query.limit(limit)
        if offset is not None:
            query = query.offset(offset)
        return query

    def _build_query(
        self,
        id: int | None = None,
        recipient_id: int | None = None,
        type: NotificationType | None = None,
        status: NotificationStatus | None = None,
    ) -> Select[tuple[Notification]]:
        query = select(Notification)

        if id is not None:
            query = query.where(Notification.id == id)
        if recipient_id is not None:
            query = query.where(Notification.recipient_id == recipient_id)
        if type is not None:
            query = query.where(Notification.type == type)
        if status is not None:
            query = query.where(Notification.status == status)

        return query

    async def get(
        self,
        id: int | None = None,
        recipient_id: int | None = None,
        type: NotificationType | None = None,
        status: NotificationStatus | None = None,
    ) -> Notification | None:
        query = self._build_query(
            id=id,
            recipient_id=recipient_id,
            type=type,
            status=status,
        )
        return await self._db.scalar(query)

    async def find_many(
        self,
        id: int | None = None,
        recipient_id: int | None = None,
        type: NotificationType | None = None,
        status: NotificationStatus | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> Sequence[Notification]:
        query = self._build_query(
            id=id,
            recipient_id=recipient_id,
            type=type,
            status=status,
        )
        query = self._apply_pagination(query, limit=limit, offset=offset)

        result = await self._db.scalars(query)
        return result.all()

    async def add(
        self,
        sender_id: int,
        recipient_id: int,
        type: NotificationType,
        title: str,
        message: str,
        target_id: int,
        target_type: NotificationTargetType,
        response: NotificationResponse | None = None,
        status: NotificationStatus = NotificationStatus.UNREAD,
    ) -> Notification:
        notification = Notification(
            sender_id=sender_id,
            recipient_id=recipient_id,
            type=type,
            title=title,
            message=message,
            target_id=target_id,
            target_type=target_type,
            response=response,
            status=status,
        )
        self._db.add(notification)
        await self._db.flush()
        return notification

    async def mark_all_unread_as_read(
        self,
        recipient_id: int,
    ) -> Notification:
        query = (
            update(Notification)
            .where(
                Notification.recipient_id == recipient_id,
                Notification.status == NotificationStatus.UNREAD,
            )
            .values(status=NotificationStatus.READ)
        )
        result = await self._db.execute(query)
        await self._db.flush()

        return result.rowcount  # type: ignore[attr-defined]

    async def count_unread(self, recipient_id: int) -> int:
        query = select(func.count(Notification.id)).where(
            Notification.recipient_id == recipient_id,
            Notification.status == NotificationStatus.UNREAD,
        )
        return await self._db.scalar(query) or 0
