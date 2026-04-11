from sqlalchemy import Select, Update, select, update

from app.models import Notification
from app.schemas.enum import NotificationStatus, NotificationType


class NotificationQueries:
    """
    Query builders for Notification-related operations.

    Provides reusable Select[tuple[Notification]] filters (by ID, recipient,
    type, status) and an UPDATE builder to mark all unread notifications as read.
    """

    @staticmethod
    def get_notification(
        id: int | None = None,
        recipient_id: int | None = None,
        type: NotificationType | None = None,
        status: NotificationStatus | None = None,
    ) -> Select[tuple[Notification]]:
        """
        Builds a query to filter notifications by multiple criteria.

        Args:
            id: Filter by notification ID.
            recipient_id: Filter by recipient (user) ID.
            type: Filter by notification type.
            status: Filter by notification status.

        Returns:
            Select[tuple[Notification]] for matching notifications.
        """
        base = select(Notification)

        if id is not None:
            base = base.where(Notification.id == id)
        if recipient_id is not None:
            base = base.where(Notification.recipient_id == recipient_id)
        if type is not None:
            base = base.where(Notification.type == type)
        if status is not None:
            base = base.where(Notification.status == status)

        return base

    @staticmethod
    def mark_all_unread_as_read_query(recipient_id: int) -> Update:
        """
        Builds an UPDATE query to mark all UNREAD notifications as READ for a user.

        Returns an `Update` object that can be executed by the session:
        - sets `status = READ`
        - for notifications where:
          - recipient_id matches and
          - status is UNREAD.

        Args:
            recipient_id: ID of the recipient user.

        Returns:
            Update query for marking notifications as read.
        """
        return (
            update(Notification)
            .where(
                Notification.recipient_id == recipient_id,
                Notification.status == NotificationStatus.UNREAD,
            )
            .values(status=NotificationStatus.READ)
        )
