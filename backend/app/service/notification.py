from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.log import get_logger
from app.db import db_helper
from app.es import ElasticsearchIndexer, get_es_indexer
from app.models import Notification as NotificationModel
from app.models import User as UserModel
from app.schemas import (
    NotificationRead,
)
from app.schemas.enum import (
    NotificationResponse,
    NotificationStatus,
    NotificationTargetType,
    NotificationType,
)

from .base import BaseService
from .exceptions import notifi_exc
from .sse import get_sse_service
from .utils import Indexer

logger = get_logger("service.notification")


class NotificationService(BaseService):
    """Service for managing user notifications and real-time messaging.

    This service handles creation, retrieval, and management of notifications
    for users. It integrates with Server-Sent Events (SSE) for real-time
    notification delivery and Elasticsearch for search functionality.

    Features:
    - Create notifications for various user actions and system events
    - Retrieve notifications with filtering and pagination
    - Mark notifications as read/unread
    - Real-time notification delivery via SSE
    - Elasticsearch indexing for notification search
    - Cache invalidation for improved performance

    Attributes:
        _db (AsyncSession): SQLAlchemy async database session
        _sse_svc (SSEService): Server-Sent Events service for real-time delivery
        _indexer (Indexer): Elasticsearch indexer wrapper

    Example:
        ```python
        notification_service = NotificationService(db_session, es_indexer)
        notification = await notification_service.create_notification(
            sender_id=1,
            recipient_id=2,
            type=NotificationType.TASK_ASSIGNED,
            title="Task Assigned",
            message="You have been assigned to a task",
            target_id=1,
            target_type=NotificationTargetType.TASK
        )
        ```
    """

    def __init__(
        self,
        db: AsyncSession,
        indexer: ElasticsearchIndexer,
    ) -> None:
        """Initialize NotificationService
            with database session and Elasticsearch indexer.

        Args:
            db: SQLAlchemy async database session
            indexer: Elasticsearch indexer instance
        """
        super().__init__(db)
        self._sse_svc = get_sse_service()
        self._indexer = Indexer(indexer)

    async def _get_notification(
        self, notification_id: int, user_id: int | None = None
    ) -> NotificationModel:
        result = await self._db.scalar(
            self._notification_queries.get_notification(
                id=notification_id, recipient_id=user_id
            )
        )
        if result is None:
            raise notifi_exc.NotificationNotFoundError(message="Notification not found")
        return result

    async def _get_notification_by_id_and_recipient(
        self, notification_id: int, user_id: int
    ) -> NotificationModel:
        result = await self._db.scalar(
            self._notification_queries.get_notification(
                id=notification_id, recipient_id=user_id
            )
        )
        if result is None:
            raise notifi_exc.NotificationNotFoundError(message="Notification not found")
        return result

    async def _get_notifications(self, user_id: int) -> list[NotificationModel]:
        result = await self._db.scalars(
            self._notification_queries.get_notification(recipient_id=user_id)
        )
        return list(result.all())

    async def _add_data_to_notification(
        self,
        sender_id: int,
        recipient_id: int,
        type: NotificationType,
        title: str,
        message: str,
        target_id: int,
        target_type: NotificationTargetType,
    ) -> NotificationModel:
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
        await self._indexer.index(notification)
        await self._db.refresh(notification)
        return notification

    async def create_notification(
        self,
        sender_id: int,
        recipient_id: int,
        type: NotificationType,
        title: str,
        message: str,
        target_id: int,
        target_type: NotificationTargetType,
        sphere: str | None = None,
        new_level: int | None = None,
    ) -> NotificationRead:
        notification = await self._add_data_to_notification(
            sender_id=sender_id,
            recipient_id=recipient_id,
            type=type,
            title=title,
            message=message,
            target_id=target_id,
            target_type=target_type,
        )

        if type == NotificationType.LEVEL_UP:
            await self._sse_svc.send_notification(
                user_id=recipient_id,
                event_type="level_up",
                data={
                    "sphere": sphere,
                    "new_level": new_level,
                    "title": title,
                },
            )
        else:
            await self._sse_svc.send_notification(
                user_id=notification.recipient_id,
                event_type="notification",
                data={
                    "id": notification.id,
                    "type": notification.type.value,
                    "title": notification.title,
                    "message": notification.message,
                    "target_id": notification.target_id,
                    "target_type": notification.target_type.value,
                    "status": notification.status.value,
                    "created_at": notification.created_at.isoformat()
                    if notification.created_at
                    else None,
                },
            )

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
        query = self._notification_queries.get_notification(
            recipient_id=user_id, status=status, type=type
        )
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
            self._notification_queries.mark_all_unread_as_read_query(
                recipient_id=user_id
            )
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

    async def notify_group_join(
        self,
        requester_id: int,
        user_id: int,
        group_id: int,
        group_name: str,
    ) -> NotificationRead:
        return await self.create_notification(
            sender_id=requester_id,
            recipient_id=user_id,
            type=NotificationType.GROUP_JOIN,
            title="Joined group",
            message=f"User joined the group '{group_name}'",
            target_id=group_id,
            target_type=NotificationTargetType.GROUP,
        )

    async def notify_join_request_created(
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
            title="New join request",
            message=f"User wants to join the group '{group_name}'",
            target_id=group_id,
            target_type=NotificationTargetType.GROUP,
        )

    async def notify_join_request_approved(
        self,
        admin_id: int,
        user_id: int,
        group_id: int,
        group_name: str,
    ) -> NotificationRead:
        return await self.create_notification(
            sender_id=admin_id,
            recipient_id=user_id,
            type=NotificationType.GROUP_JOIN,
            title="Join request approved",
            message=f"Your request to join '{group_name}' was approved",
            target_id=group_id,
            target_type=NotificationTargetType.GROUP,
        )

    async def notify_join_request_rejected(
        self,
        admin_id: int,
        user_id: int,
        group_id: int,
        group_name: str,
    ) -> NotificationRead:
        return await self.create_notification(
            sender_id=admin_id,
            recipient_id=user_id,
            type=NotificationType.GROUP_JOIN,
            title="Join request rejected",
            message=f"Your request to join '{group_name}' was rejected",
            target_id=group_id,
            target_type=NotificationTargetType.GROUP,
        )

    async def notify_level_up(
        self,
        user_id: int,
        sphere: str,
        new_level: int,
        title: str,
    ) -> NotificationRead:
        return await self.create_notification(
            sender_id=0,
            recipient_id=user_id,
            type=NotificationType.LEVEL_UP,
            title="Level Up!",
            message=f"You reached level {new_level} in {sphere}! Title: {title}",
            target_id=user_id,
            target_type=NotificationTargetType.USER,
            sphere=sphere,
            new_level=new_level,
        )


def get_notification_service(
    db: AsyncSession = Depends(db_helper.get_session),
    indexer: ElasticsearchIndexer = Depends(get_es_indexer),
) -> NotificationService:
    return NotificationService(
        db=db,
        indexer=indexer,
    )
