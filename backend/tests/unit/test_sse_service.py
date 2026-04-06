from unittest.mock import AsyncMock, MagicMock, patch

from app.service.sse import SSEService


class TestSSEConnect:
    async def test_connect_returns_queue(self):
        mock_queue = MagicMock()
        with patch("app.service.sse.sse_manager") as mock_manager:
            mock_manager.connect = AsyncMock(return_value=mock_queue)
            svc = SSEService()
            result = await svc.connect(user_id=1)
            assert result == mock_queue
            mock_manager.connect.assert_called_once_with(1)


class TestSSEDisconnect:
    async def test_disconnect_calls_manager(self):
        with patch("app.service.sse.sse_manager") as mock_manager:
            mock_manager.disconnect = AsyncMock()
            svc = SSEService()
            await svc.disconnect(user_id=1)
            mock_manager.disconnect.assert_called_once_with(1)


class TestSSESendNotification:
    async def test_send_notification_calls_publish(self):
        with patch("app.service.sse.sse_manager") as mock_manager:
            mock_manager.publish = AsyncMock()
            svc = SSEService()
            await svc.send_notification(
                user_id=1, event_type="notification", data={"key": "value"}
            )
            mock_manager.publish.assert_called_once_with(
                user_id=1, event_type="notification", data={"key": "value"}
            )


class TestSSEEventGenerator:
    async def test_event_generator_yields_messages(self):
        mock_queue = AsyncMock()
        mock_queue.get = AsyncMock(return_value='{"test": "data"}')

        with patch("app.service.sse.sse_manager") as mock_manager:
            mock_manager.connect = AsyncMock(return_value=mock_queue)

            svc = SSEService()
            gen = svc.event_generator(user_id=1)

            result = await gen.__anext__()
            assert "event:" in result


class TestGetSSEService:
    def test_get_sse_service_returns_instance(self):
        from app.service.sse import get_sse_service

        result = get_sse_service()
        assert isinstance(result, SSEService)
