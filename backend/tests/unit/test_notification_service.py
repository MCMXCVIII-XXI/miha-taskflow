from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.schemas.enum.notification import NotificationTargetType, NotificationType
from app.service.notification import NotificationService


@pytest.fixture
def mock_notification_transaction():
    mock = MagicMock()
    mock.create_notification = AsyncMock()
    return mock


class TestNotifyLevelUp:
    async def test_notify_group_invite_returns_notification(
        self, mock_db: AsyncMock, mock_indexer, mock_notification_transaction
    ):

        from app.schemas.enum.notification import (
            NotificationResponse,
            NotificationStatus,
        )

        mock_notification = MagicMock()
        mock_notification.id = 1
        mock_notification.sender_id = 1
        mock_notification.recipient_id = 2
        mock_notification.type = NotificationType.GROUP_INVITE
        mock_notification.title = "Group Invite"
        mock_notification.message = "You are invited"
        mock_notification.target_id = 1
        mock_notification.target_type = NotificationTargetType.GROUP
        mock_notification.response = NotificationResponse.WAITING
        mock_notification.status = NotificationStatus.UNREAD
        mock_notification.created_at = datetime.now(tz=UTC)

        mock_notification_transaction.create_notification.return_value = (
            mock_notification
        )

        mock_sse = AsyncMock()
        mock_sse.send_notification = AsyncMock()

        with (
            patch("app.service.notification.get_sse_service", return_value=mock_sse),
            patch("app.service.notification.logger"),
        ):
            svc = NotificationService(
                mock_db,
                mock_indexer,
                notification_transaction=mock_notification_transaction,
            )
            svc._sse_svc = mock_sse

            await svc.notify_group_invite(
                inviter_id=1,
                invitee_id=2,
                group_id=1,
                group_name="Test Group",
            )

            mock_notification_transaction.create_notification.assert_called_once()


class TestNotifyTaskInvite:
    async def test_notify_task_invite_returns_notification(
        self, mock_db: AsyncMock, mock_indexer, mock_notification_transaction
    ):

        from app.schemas.enum.notification import (
            NotificationResponse,
            NotificationStatus,
        )

        mock_notification = MagicMock()
        mock_notification.id = 1
        mock_notification.sender_id = 1
        mock_notification.recipient_id = 2
        mock_notification.type = NotificationType.TASK_INVITE
        mock_notification.title = "Task Invite"
        mock_notification.message = "You are invited"
        mock_notification.target_id = 1
        mock_notification.target_type = NotificationTargetType.TASK
        mock_notification.response = NotificationResponse.WAITING
        mock_notification.status = NotificationStatus.UNREAD
        mock_notification.created_at = datetime.now(tz=UTC)

        mock_notification_transaction.create_notification.return_value = (
            mock_notification
        )

        mock_sse = AsyncMock()
        mock_sse.send_notification = AsyncMock()

        with (
            patch("app.service.notification.get_sse_service", return_value=mock_sse),
            patch("app.service.notification.logger"),
        ):
            svc = NotificationService(
                mock_db,
                mock_indexer,
                notification_transaction=mock_notification_transaction,
            )
            svc._sse_svc = mock_sse

            await svc.notify_task_invite(
                inviter_id=1,
                invitee_id=2,
                task_id=1,
                task_title="Test Task",
            )

            mock_notification_transaction.create_notification.assert_called_once()
