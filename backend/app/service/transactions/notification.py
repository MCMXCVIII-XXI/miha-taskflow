from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.log import logging
from app.db import db_helper
from app.models import Notification as NotificationModel
from app.models import User as UserModel
from app.repositories import UnitOfWork
from app.schemas.enum import (
    NotificationResponse,
    NotificationStatus,
    NotificationTargetType,
    NotificationType,
)

from ..exceptions import notifi_exc
from .base import BaseTransaction

logger = logging.get_logger(__name__)


class NotificationTransaction(BaseTransaction):
    def __init__(
        self,
        uow_class: type[UnitOfWork],
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        super().__init__(uow_class=uow_class, session_factory=session_factory)

    async def create_notification(
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
    ) -> NotificationModel:
        async with self._create_uow() as uow:
            notification = await uow.notification.add(
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
        return notification

    async def get_my_notification(
        self, current_user: UserModel, notification_id: int
    ) -> NotificationModel:
        async with self._create_uow() as uow:
            notification = await uow.notification.get(
                id=notification_id,
                recipient_id=current_user.id,
            )
            if not notification:
                raise notifi_exc.NotificationNotFoundError(
                    message=f"Notification {notification_id} not found"
                )

            notification.status = NotificationStatus.READ

        return notification

    async def respond_to_notification(
        self,
        notification_id: int,
        user_id: int,
        response: NotificationResponse,
    ) -> NotificationModel:
        async with self._create_uow() as uow:
            notification = await uow.notification.get(
                id=notification_id,
                recipient_id=user_id,
            )
            if not notification:
                raise notifi_exc.NotificationNotFoundError(
                    message=f"Notification {notification_id} not found"
                )
            if notification.type not in [
                NotificationType.GROUP_INVITE,
                NotificationType.GROUP_JOIN,
                NotificationType.TASK_INVITE,
            ]:
                raise notifi_exc.NotificationNotActionableError(
                    message="This notification cannot be responded to"
                )

            notification.response = response
            notification.status = NotificationStatus.READ

        return notification

    async def mark_as_read(
        self, notification_id: int, user_id: int
    ) -> NotificationModel:
        async with self._create_uow() as uow:
            notification = await uow.notification.get(
                id=notification_id,
                recipient_id=user_id,
            )
            if not notification:
                logger.error(
                    f"Notification {notification_id} not found for user {user_id}"
                )
                raise notifi_exc.NotificationNotFoundError(
                    message=f"Notification {notification_id} \
                        not found for user {user_id}"
                )

            notification.status = NotificationStatus.READ

        return notification


def get_notification_transaction() -> NotificationTransaction:
    return NotificationTransaction(
        uow_class=UnitOfWork,
        session_factory=db_helper.session_factory,
    )
