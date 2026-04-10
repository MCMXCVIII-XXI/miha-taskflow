from unittest.mock import AsyncMock, MagicMock, patch

from app.schemas.enum import NotificationType
from app.service.notification import NotificationService


class TestNotifyLevelUp:
    async def test_notify_group_invite_returns_notification(
        self, mock_db: AsyncMock, mock_indexer
    ):
        mock_sse = AsyncMock()
        mock_sse.send_notification = AsyncMock()

        with patch("app.service.notification.get_sse_service", return_value=mock_sse):
            svc = NotificationService(mock_db, mock_indexer)
            svc._sse_svc = mock_sse

            with patch.object(
                svc, "create_notification", new=AsyncMock()
            ) as mock_create:
                mock_create.return_value = MagicMock()
                await svc.notify_group_invite(
                    inviter_id=1,
                    invitee_id=2,
                    group_id=1,
                    group_name="Test Group",
                )

                mock_create.assert_called_once()
                call_kwargs = mock_create.call_args.kwargs
                assert call_kwargs["type"] == NotificationType.GROUP_INVITE
                assert call_kwargs["recipient_id"] == 2


class TestNotifyTaskInvite:
    async def test_notify_task_invite_returns_notification(
        self, mock_db: AsyncMock, mock_indexer
    ):
        mock_sse = AsyncMock()
        mock_sse.send_notification = AsyncMock()

        with patch("app.service.notification.get_sse_service", return_value=mock_sse):
            svc = NotificationService(mock_db, mock_indexer)
            svc._sse_svc = mock_sse

            with patch.object(
                svc, "create_notification", new=AsyncMock()
            ) as mock_create:
                mock_create.return_value = MagicMock()
                await svc.notify_task_invite(
                    inviter_id=1,
                    invitee_id=2,
                    task_id=1,
                    task_title="Test Task",
                )

                mock_create.assert_called_once()
                call_kwargs = mock_create.call_args.kwargs
                assert call_kwargs["type"] == NotificationType.TASK_INVITE
                assert call_kwargs["recipient_id"] == 2


class TestGetNotificationService:
    def test_get_notification_service_returns_instance(self, mock_db: AsyncMock):
        from app.service.notification import get_notification_service

        result = get_notification_service(mock_db)
        assert isinstance(result, NotificationService)
