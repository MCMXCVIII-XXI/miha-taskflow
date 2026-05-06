"""Notification service for user notifications and real-time messaging.

This module provides the NotificationService class for managing user notifications,
including creation, retrieval, status updates, and response handling.

**Key Components:**
* `NotificationService`: Main service class for notification operations;
* `get_notification_service`: FastAPI dependency injection factory.

**Dependencies:**
* `NotificationRepository`: Notification data access layer;
* `UnitOfWork`: Transaction management (via BaseService);
* `ElasticsearchIndexer`: Search index management;
* `SSEService`: Server-Sent Events for real-time delivery.

**Usage Example:**
    ```python
    from app.service.notification import get_notification_service

    @router.get("/notifications")
    async def get_notifications(
        notification_svc: NotificationService = Depends(get_notification_service),
        current_user: User = Depends(get_current_user)
    ):
        return await notification_svc.get_my_notifications(current_user)
    ```

**Notes:**
- Notifications support various types:
    group invites, task invites, comments, ratings, etc.;
- Real-time delivery via SSE for connected clients;
- Notifications are indexed in Elasticsearch for search functionality;
- Supports marking as read and responding to actionable notifications.
"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.log import logging
from app.core.metrics import METRICS
from app.db import db_helper
from app.es import ElasticsearchIndexer, get_es_indexer
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
from .transactions.notification import (
    NotificationTransaction,
    get_notification_transaction,
)
from .utils import Indexer

logger = logging.get_logger(__name__)


class NotificationService(BaseService):
    """Service for managing user notifications and real-time messaging.

    Handles creation, retrieval, and management of notifications for users.
    Integrates with Server-Sent Events (SSE) for real-time notification
    delivery and Elasticsearch for search functionality.

    Attributes:
        _db (AsyncSession): SQLAlchemy async database session
        _sse_svc: Server-Sent Events service for real-time delivery
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
        notification_transaction: NotificationTransaction,
    ) -> None:
        """Initialize NotificationService with database session and
            Elasticsearch indexer.

        Args:
            db: SQLAlchemy async database session
            indexer: Elasticsearch indexer instance
        """
        super().__init__(db=db)
        self._sse_svc = get_sse_service()
        self._indexer = Indexer(indexer)
        self._notification_transaction = notification_transaction

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
        """Create and send a new notification to a user.

        Creates a notification with the specified parameters, indexes it in
        Elasticsearch, and sends it via SSE to the recipient if they're connected.

        Args:
            sender_id: ID of the user who triggered the notification
                Type: int
            recipient_id: ID of the user who receives the notification
                Type: int
            type: Type of notification (e.g., TASK_INVITE, GROUP_JOIN, COMMENT)
                Type: NotificationType
            title: Notification title
                Type: str
            message: Notification message body
                Type: str
            target_id: ID of the related entity (task, group, user)
                Type: int
            target_type: Type of the target entity
                Type: NotificationTargetType
            sphere: Optional sphere for level-up notifications
                Type: str | None
                Defaults to None
            new_level: Optional new level for level-up notifications
                Type: int | None
                Defaults to None

        Returns:
            NotificationRead: Created notification serialized according to
                NotificationRead schema

        Example:
            ```python
            notification = await notification_svc.create_notification(
                sender_id=1,
                recipient_id=2,
                type=NotificationType.TASK_INVITE,
                title="Task Invitation",
                message="You've been invited to task 'Fix bug'",
                target_id=123,
                target_type=NotificationTargetType.TASK
            )
            ```
        """
        response = (
            NotificationResponse.WAITING
            if type in [NotificationType.GROUP_JOIN, NotificationType.TASK_INVITE]
            else NotificationResponse.ACCEPT
        )

        notification = await self._notification_transaction.create_notification(
            sender_id=sender_id,
            recipient_id=recipient_id,
            type=type,
            title=title,
            message=message,
            target_id=target_id,
            target_type=target_type,
            response=response,
            status=NotificationStatus.UNREAD,
        )

        await self._indexer.index(notification)

        logger.info(
            "Notification created: id={notification_id}, type={type}, \
                recipient_id={recipient_id}",
            notification_id=notification.id,
            type=type.value,
            recipient_id=recipient_id,
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
                    "created_at": (
                        notification.created_at.isoformat()
                        if notification.created_at
                        else None
                    ),
                },
            )
        METRICS.NOTIFICATION_SENT_TOTAL.labels(type=type.value, status="success").inc()
        return NotificationRead.model_validate(notification)

    async def get_my_notifications(
        self, current_user: UserModel
    ) -> list[NotificationRead]:
        """Retrieve all notifications for the current user.

        Fetches all notifications where the current user is the recipient,
        regardless of status.

        Args:
            current_user (UserModel):
                The authenticated user requesting their notifications

        Returns:
            list[NotificationRead]: List of notifications

        Example:
            ```python
            notifications = await notification_svc.get_my_notifications(current_user)
            ```
        """
        notifications = await self._notification_repo.find_many(
            recipient_id=current_user.id,
        )

        logger.info(
            "User notifications retrieved: user_id={user_id}, count={count}",
            user_id=current_user.id,
            count=len(notifications),
        )

        return [
            NotificationRead.model_validate(notification)
            for notification in notifications
        ]

    async def get_my_notification(
        self, current_user: UserModel, notification_id: int
    ) -> NotificationRead:
        """Retrieve a specific notification and mark it as read.

        Fetches a notification by ID where the current user is the recipient,
        and automatically marks it as read.

        Args:
            current_user (UserModel): The authenticated user
            notification_id (int): ID of the notification to retrieve (must be > 0)

        Returns:
            NotificationRead: Single notification

        Example:
            ```python
            notification = await notification_svc.get_my_notification(user, 123)
            ```
        """
        notification = await self._notification_transaction.get_my_notification(
            current_user=current_user, notification_id=notification_id
        )

        logger.info(
            "Notification retrieved and marked read: "
            "id={notification_id}, user_id={user_id}",
            notification_id=notification_id,
            user_id=current_user.id,
        )

        return NotificationRead.model_validate(notification)

    async def get_notification(
        self, notification_id: int, user_id: int
    ) -> NotificationRead:
        """Retrieve a specific notification by ID and recipient.

        Fetches a notification by ID without modifying its read status.

        Args:
            notification_id (int): ID of the notification to retrieve (must be > 0)
            user_id (int): ID of the user who should own the notification

        Returns:
            NotificationRead: Single notification

        Example:
            ```python
            notification = await notification_svc.get_notification(123, user_id)
            ```
        """
        notification = await self._notification_repo.get(
            id=notification_id,
            recipient_id=user_id,
        )
        if not notification:
            raise notifi_exc.NotificationNotFoundError(
                message=f"Notification {notification_id} not found"
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
        """Retrieve notifications for a user with filtering and pagination.

        Fetches notifications with optional filters for status and type,
        sorted by creation date (newest first).

        Args:
            user_id (int): ID of the user to get notifications for
            status (NotificationStatus | None):
                Optional filter by notification status (READ, UNREAD)
            type (NotificationType | None):
                Optional filter by notification type
            limit (int): Maximum number of notifications to return
            offset (int): Number of notifications to skip for pagination

        Returns:
            list[NotificationRead]: List of notifications

        Example:
            ```python
            notifications = await notification_svc.get_notifications(
                user_id=1,
                status=NotificationStatus.UNREAD,
                limit=10
            )
            ```
        """
        notifications = await self._notification_repo.find_many(
            recipient_id=user_id,
            status=status,
            type=type,
            limit=limit,
            offset=offset,
        )
        notifications = sorted(notifications, key=lambda n: n.created_at, reverse=True)

        logger.info(
            "Notifications retrieved: user_id={user_id}, "
            "count={count}, status={status}",
            user_id=user_id,
            count=len(notifications),
            status=status.value if status else "all",
        )

        return [NotificationRead.model_validate(n) for n in notifications]

    async def mark_as_read(
        self, notification_id: int, user_id: int
    ) -> NotificationRead:
        """Mark a specific notification as read.

            Updates the notification status to READ for the specified notification
            and user.

        Args:
            notification_id (int): ID of the notification to mark as read (must be > 0)
            user_id (int): ID of the user who owns the notification

        Returns:
            list[NotificationRead]: List of notifications

        Example:
            ```python
            notification = await notification_svc.mark_as_read(123, user_id)
            ```
        """
        notification = await self._notification_transaction.mark_as_read(
            notification_id=notification_id, user_id=user_id
        )

        logger.info(
            "Notification marked as read: id={notification_id}, user_id={user_id}",
            notification_id=notification_id,
            user_id=user_id,
        )
        METRICS.NOTIFICATION_SENT_TOTAL.labels(
            type="notification", status="success"
        ).inc()
        return NotificationRead.model_validate(notification)

    async def mark_all_as_read(self, user_id: int) -> int:
        """Mark all unread notifications as read for a user.

        Updates the status of all unread notifications to READ for the
        specified user.

        Args:
            user_id (int): ID of the user whose notifications to mark as read

        Returns:
            int: Number of notifications marked as read (currently returns 0)

        Example:
            ```python
            count = await notification_svc.mark_all_as_read(user_id)
            ```
        """
        result = await self._notification_repo.mark_all_unread_as_read(
            recipient_id=user_id,
        )

        logger.info(
            "All notifications marked as read: user_id={user_id}",
            user_id=user_id,
        )
        METRICS.NOTIFICATION_SENT_TOTAL.labels(
            type="notification",
            status="success",
        ).inc()
        return result  # type: ignore[return-value]

    async def respond_to_notification(
        self,
        notification_id: int,
        user_id: int,
        response: NotificationResponse,
    ) -> NotificationRead:
        """Respond to an actionable notification (invite/request).

        Updates the notification response and marks it as read. Only applicable
        to notifications that support responses:
            GROUP_INVITE, GROUP_JOIN, TASK_INVITE.

        Args:
            notification_id (int): ID of the notification to respond to (must be > 0)
            user_id (int): ID of the user responding to the notification
            response (NotificationResponse): The response (ACCEPT or REJECT)

        Returns:
            NotificationRead: Single notification

        Example:
            ```python
            notification = await notification_svc.respond_to_notification(
                123, user_id, NotificationResponse.ACCEPT
            )
            ```
        """
        notification = await self._notification_transaction.respond_to_notification(
            notification_id=notification_id,
            user_id=user_id,
            response=response,
        )

        logger.info(
            "Notification responded: id={notification_id}, response={response}",
            notification_id=notification_id,
            response=response.value,
        )
        METRICS.NOTIFICATION_SENT_TOTAL.labels(
            type="notification", status="success"
        ).inc()
        return NotificationRead.model_validate(notification)

    async def notify_group_invite(
        self,
        inviter_id: int,
        invitee_id: int,
        group_id: int,
        group_name: str,
    ) -> NotificationRead:
        """Send a group invitation notification.

        Args:
            inviter_id (int): ID of user sending the invitation
            invitee_id (int): ID of user receiving the invitation
            group_id (int): ID of the group
            group_name (str): Name of the group

        Returns:
            NotificationRead: Created notification
        """
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
        """Send a group join request notification to admin.

        Args:
            requester_id (int): ID of user requesting to join
            admin_id (int): ID of group admin
            group_id (int): ID of the group
            group_name (str): Name of the group

        Returns:
            NotificationRead: Created notification
        """
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
        """Send a task invitation notification.

        Args:
            inviter_id (int): ID of user sending the invitation
            invitee_id (int): ID of user receiving the invitation
            task_id (int): ID of the task
            task_title (str): Title of the task

        Returns:
            NotificationRead: Created notification
        """
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
        """Send a new comment notification.

        Args:
            commenter_id (int): ID of user who commented
            recipient_id (int): ID of user to notify
            task_id (int): ID of the task
            task_title (str): Title of the task

        Returns:
            NotificationRead: Created notification
        """
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
        """Send a mention notification.

        Args:
            mentioner_id (int): ID of user who mentioned
            mentioned_id (int): ID of user who was mentioned
            task_id (int): ID of the task
            task_title (str): Title of the task
            username (str): Username of the mentioner

        Returns:
            NotificationRead: Created notification
        """
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
        """Send a new follower notification.

        Args:
            follower_id (int): ID of new follower
            following_id (int): ID of user being followed
            username (str): Username of the follower

        Returns:
            NotificationRead: Created notification
        """
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
        """Send a new rating notification.

        Args:
            rater_id (int): ID of user who gave the rating
            recipient_id (int): ID of user receiving the notification
            target_id (int): ID of rated task or group
            target_type (NotificationTargetType): Type of rated entity
            rating (int): Rating score

        Returns:
            NotificationRead: Created notification
        """
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
        """Send a group join notification.

        Args:
            requester_id (int): ID of user who joined
            user_id (int): ID of user to notify
            group_id (int): ID of the group
            group_name (str): Name of the group

        Returns:
            NotificationRead: Created notification
        """
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
        """Send a join request created notification.

        Args:
            requester_id (int): ID of user who created request
            admin_id (int): ID of group admin
            group_id (int): ID of the group
            group_name (str): Name of the group

        Returns:
            NotificationRead: Created notification
        """
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
        """Send a join request approved notification.

        Args:
            admin_id (int): ID of admin who approved
            user_id (int): ID of user whose request was approved
            group_id (int): ID of the group
            group_name (str): Name of the group

        Returns:
            NotificationRead: Created notification
        """
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
        """Send a join request rejected notification.

        Args:
            admin_id (int): ID of admin who rejected
            user_id (int): ID of user whose request was rejected
            group_id (int): ID of the group
            group_name (str): Name of the group

        Returns:
            NotificationRead: Created notification
        """
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
        """Send a level up notification.

        Args:
            user_id (int): ID of user who leveled up
            sphere (str): Sphere in which user leveled up
            new_level (int): New level achieved
            title (str): Title earned at new level

        Returns:
            NotificationRead: Created notification
        """
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
    notification_transaction: NotificationTransaction = Depends(
        get_notification_transaction
    ),
) -> NotificationService:
    """Create NotificationService instance with dependency injection.

    Factory function for FastAPI dependency injection that creates and configures
    a NotificationService instance with all required dependencies.

    Args:
        db (AsyncSession): Database session from FastAPI dependency injection.
        indexer (ElasticsearchIndexer):
            Elasticsearch client from FastAPI dependency injection.

    Returns:
        NotificationService: Configured notification service instance

    Example:
        ```python
        @router.get("/notifications")
        async def get_notifications(
            notification_svc: NotificationService = Depends(get_notification_service),
            current_user: User = Depends(get_current_user)
        ):
            return await notification_svc.get_my_notifications(current_user)
        ```
    """
    return NotificationService(
        db=db,
        indexer=indexer,
        notification_transaction=notification_transaction,
    )
