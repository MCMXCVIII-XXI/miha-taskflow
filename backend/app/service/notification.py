from fastapi import Depends
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.log import get_logger
from app.db import db_helper
from app.models import Notification as NotificationModel
from app.models import User as UserModel
from app.schemas import (
    NotificationRead,
    NotificationResponse,
    NotificationStatus,
    NotificationTargetType,
    NotificationType,
)

from .base import BaseService
from .exceptions import notifi_exc

logger = get_logger("service.notification")


class NotificationService(BaseService):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db)

    async def _get_notification(
        self, notification_id: int, user_id: int | None = None
    ) -> NotificationModel:
        query = select(NotificationModel).where(
            NotificationModel.id == notification_id,
        )
        if user_id:
            query = query.where(NotificationModel.recipient_id == user_id)
        result = await self._db.scalar(query)
        if result is None:
            raise notifi_exc.NotificationNotFoundError(message="Notification not found")
        return result

    async def _get_notification_by_id_and_recipient(
        self, notification_id: int, user_id: int
    ) -> NotificationModel:
        query = select(NotificationModel).where(
            NotificationModel.id == notification_id,
            NotificationModel.recipient_id == user_id,
        )
        result = await self._db.scalar(query)
        if result is None:
            raise notifi_exc.NotificationNotFoundError(message="Notification not found")
        return result

    async def _get_notifications(self, user_id: int) -> list[NotificationModel]:
        query = select(NotificationModel).where(
            NotificationModel.recipient_id == user_id
        )
        result = await self._db.scalars(query)
        return list(result.all())

    async def create_notification(
        self,
        sender_id: int,
        recipient_id: int,
        type: NotificationType,
        title: str,
        message: str,
        target_id: int,
        target_type: NotificationTargetType,
    ) -> NotificationRead:
        notification = NotificationModel(
            sender_id=sender_id,
            recipient_id=recipient_id,
            type=type,
            title=title,
            message=message,
            target_id=target_id,
            target_type=target_type,
            response=NotificationResponse.WAITING
            if type
            in [
                NotificationType.GROUP_INVITE,
                NotificationType.GROUP_JOIN,
                NotificationType.TASK_INVITE,
            ]
            else NotificationResponse.ACCEPT,
            status=NotificationStatus.UNREAD,
        )
        self._db.add(notification)
        await self._db.commit()
        await self._db.refresh(notification)
        return NotificationRead.model_validate(notification)

    async def get_my_notifications(
        self, current_user: UserModel
    ) -> list[NotificationRead]:
        notifications = await self._get_notifications(current_user.id)
        return [
            NotificationRead.model_validate(notification)
            for notification in notifications
        ]

    async def get_my_notification(
        self, current_user: UserModel, notification_id: int
    ) -> NotificationRead:
        notification = await self._get_notification_by_id_and_recipient(
            notification_id, current_user.id
        )
        notification.status = NotificationStatus.READ
        await self._db.commit()
        return NotificationRead.model_validate(notification)

    async def get_notification(
        self, notification_id: int, user_id: int
    ) -> NotificationRead:
        notification = await self._get_notification_by_id_and_recipient(
            notification_id, user_id
        )
        return NotificationRead.model_validate(notification)

    async def get_notifications(
        self,
        user_id: int,
        status: NotificationStatus | None = None,
        type: NotificationType | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[NotificationRead]:
        query = select(NotificationModel).where(
            NotificationModel.recipient_id == user_id
        )
        if status:
            query = query.where(NotificationModel.status == status)
        if type:
            query = query.where(NotificationModel.type == type)
        query = query.order_by(NotificationModel.created_at.desc())
        query = query.limit(limit).offset(offset)
        result = await self._db.scalars(query)
        return [NotificationRead.model_validate(n) for n in result.all()]

    async def mark_as_read(
        self, notification_id: int, user_id: int
    ) -> NotificationRead:
        notification = await self._get_notification_by_id_and_recipient(
            notification_id, user_id
        )
        notification.status = NotificationStatus.READ
        await self._db.commit()
        return NotificationRead.model_validate(notification)

    async def mark_all_as_read(self, user_id: int) -> int:
        result = await self._db.execute(
            update(NotificationModel)
            .where(
                NotificationModel.recipient_id == user_id,
                NotificationModel.status == NotificationStatus.UNREAD,
            )
            .values(status=NotificationStatus.READ)
        )
        await self._db.commit()
        return result.rowcount  # type: ignore[attr-defined]

    async def respond_to_notification(
        self,
        notification_id: int,
        user_id: int,
        response: NotificationResponse,
    ) -> NotificationRead:
        notification = await self._get_notification_by_id_and_recipient(
            notification_id, user_id
        )

        # Проверить, что уведомление требует ответа
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
        await self._db.commit()
        return NotificationRead.model_validate(notification)

    async def notify_group_invite(
        self,
        inviter_id: int,
        invitee_id: int,
        group_id: int,
        group_name: str,
    ) -> NotificationRead:
        return await self.create_notification(
            sender_id=inviter_id,
            recipient_id=invitee_id,
            type=NotificationType.GROUP_INVITE,
            title="Invitation to a group",
            message=f"I invited you to the group '{group_name}'",
            target_id=group_id,
            target_type=NotificationTargetType.GROUP,
        )

    async def notify_group_join_request(
        self,
        requester_id: int,
        admin_id: int,
        group_id: int,
        group_name: str,
    ) -> NotificationRead:
        return await self.create_notification(
            sender_id=requester_id,
            recipient_id=admin_id,
            type=NotificationType.GROUP_JOIN,
            title="Join request",
            message=f"User wants to join the group '{group_name}'",
            target_id=group_id,
            target_type=NotificationTargetType.GROUP,
        )

    async def notify_task_invite(
        self,
        inviter_id: int,
        invitee_id: int,
        task_id: int,
        task_title: str,
    ) -> NotificationRead:
        return await self.create_notification(
            sender_id=inviter_id,
            recipient_id=invitee_id,
            type=NotificationType.TASK_INVITE,
            title="Invitation to a task",
            message=f"I invited you to the task '{task_title}'",
            target_id=task_id,
            target_type=NotificationTargetType.TASK,
        )

    async def notify_comment(
        self,
        commenter_id: int,
        recipient_id: int,
        task_id: int,
        task_title: str,
    ) -> NotificationRead:
        return await self.create_notification(
            sender_id=commenter_id,
            recipient_id=recipient_id,
            type=NotificationType.COMMENT,
            title="New comment",
            message=f"New comment to the task '{task_title}'",
            target_id=task_id,
            target_type=NotificationTargetType.TASK,
        )

    async def notify_mention(
        self,
        mentioner_id: int,
        mentioned_id: int,
        task_id: int,
        task_title: str,
        username: str,
    ) -> NotificationRead:
        return await self.create_notification(
            sender_id=mentioner_id,
            recipient_id=mentioned_id,
            type=NotificationType.MENTION,
            title="Mentioned",
            message=f"{username} mentioned you in the task '{task_title}'",
            target_id=task_id,
            target_type=NotificationTargetType.TASK,
        )

    async def notify_follow(
        self,
        follower_id: int,
        following_id: int,
        username: str,
    ) -> NotificationRead:
        return await self.create_notification(
            sender_id=follower_id,
            recipient_id=following_id,
            type=NotificationType.FOLLOW,
            title="New follower",
            message=f"{username} subscribed to you",
            target_id=follower_id,
            target_type=NotificationTargetType.USER,
        )

    async def notify_rating(
        self,
        rater_id: int,
        recipient_id: int,
        target_id: int,
        target_type: NotificationTargetType,
        rating: int,
    ) -> NotificationRead:
        target_name = "task" if target_type == NotificationTargetType.TASK else "group"
        return await self.create_notification(
            sender_id=rater_id,
            recipient_id=recipient_id,
            type=NotificationType.RATING,
            title="New rating",
            message=f"Your {target_name} received a rating of {rating}/10",
            target_id=target_id,
            target_type=target_type,
        )


def get_notification_service(
    db: AsyncSession = Depends(db_helper.get_session),
) -> NotificationService:
    return NotificationService(db)
