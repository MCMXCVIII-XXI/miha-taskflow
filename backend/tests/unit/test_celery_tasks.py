from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestBulkIndexAsync:
    """Unit tests for bulk_index_async Celery task."""

    @pytest.fixture
    def mock_outbox_service(self):
        mock = MagicMock()
        mock.bulk_index = AsyncMock(
            return_value={"success": 5, "failed": 0, "total": 5}
        )
        return mock

    @pytest.mark.asyncio
    async def test_bulk_index_task_model(self, mock_outbox_service):
        """Test bulk index with task model."""
        mock_outbox_service.bulk_index = AsyncMock(
            return_value={"success": 5, "failed": 0, "total": 5}
        )

        with patch("app.background.tasks.outbox_task_service", mock_outbox_service):
            with patch(
                "app.background.tasks.run_async",
                AsyncMock(return_value={"success": 5, "failed": 0, "total": 5}),
            ):
                from app.background import tasks

                result = await tasks.bulk_index_async(
                    "task", ids=[1, 2, 3], batch_size=10
                )

                assert "success" in result

    @pytest.mark.asyncio
    async def test_bulk_index_user_model(self, mock_outbox_service):
        """Test bulk index with user model."""
        mock_outbox_service.bulk_index = AsyncMock(
            return_value={"success": 2, "failed": 0, "total": 2}
        )

        with patch("app.background.tasks.outbox_task_service", mock_outbox_service):
            with patch(
                "app.background.tasks.run_async",
                AsyncMock(return_value={"success": 2, "failed": 0, "total": 2}),
            ):
                from app.background import tasks

                result = await tasks.bulk_index_async("user", ids=[1, 2], batch_size=5)

                assert result.get("success") == 2

    @pytest.mark.asyncio
    async def test_bulk_index_group_model(self, mock_outbox_service):
        """Test bulk index with group model."""
        mock_outbox_service.bulk_index = AsyncMock(
            return_value={"success": 1, "failed": 0, "total": 1}
        )

        with patch("app.background.tasks.outbox_task_service", mock_outbox_service):
            with patch(
                "app.background.tasks.run_async",
                AsyncMock(return_value={"success": 1, "failed": 0, "total": 1}),
            ):
                from app.background import tasks

                result = await tasks.bulk_index_async("group", batch_size=50)

                assert result.get("success") == 1

    @pytest.mark.asyncio
    async def test_bulk_index_comment_model(self, mock_outbox_service):
        """Test bulk index with comment model."""
        mock_outbox_service.bulk_index = AsyncMock(
            return_value={"success": 1, "failed": 0, "total": 1}
        )

        with patch("app.background.tasks.outbox_task_service", mock_outbox_service):
            with patch(
                "app.background.tasks.run_async",
                AsyncMock(return_value={"success": 1, "failed": 0, "total": 1}),
            ):
                from app.background import tasks

                result = await tasks.bulk_index_async(
                    "comment", ids=[1], batch_size=100
                )

                assert result.get("success") == 1

    @pytest.mark.asyncio
    async def test_bulk_index_with_ids(self, mock_outbox_service):
        """Test bulk index with specific IDs."""
        mock_outbox_service.bulk_index = AsyncMock(
            return_value={"success": 3, "failed": 0, "total": 3}
        )

        with patch("app.background.tasks.outbox_task_service", mock_outbox_service):
            with patch(
                "app.background.tasks.run_async",
                AsyncMock(return_value={"success": 3, "failed": 0, "total": 3}),
            ):
                from app.background import tasks

                result = await tasks.bulk_index_async("task", ids=[10, 20, 30])

                assert result.get("success") == 3

    @pytest.mark.asyncio
    async def test_bulk_index_default_batch_size(self, mock_outbox_service):
        """Test bulk index with default batch size."""
        mock_outbox_service.bulk_index = AsyncMock(
            return_value={"success": 1, "failed": 0, "total": 1}
        )

        with patch("app.background.tasks.outbox_task_service", mock_outbox_service):
            with patch(
                "app.background.tasks.run_async",
                AsyncMock(return_value={"success": 1, "failed": 0, "total": 1}),
            ):
                from app.background import tasks

                result = await tasks.bulk_index_async("user")

                assert result.get("success") == 1

    @pytest.mark.asyncio
    async def test_bulk_index_custom_batch_size(self, mock_outbox_service):
        """Test bulk index with custom batch size."""
        mock_outbox_service.bulk_index = AsyncMock(
            return_value={"success": 1, "failed": 0, "total": 1}
        )

        with patch("app.background.tasks.outbox_task_service", mock_outbox_service):
            with patch(
                "app.background.tasks.run_async",
                AsyncMock(return_value={"success": 1, "failed": 0, "total": 1}),
            ):
                from app.background import tasks

                result = await tasks.bulk_index_async("task", batch_size=25)

                assert result.get("success") == 1

    @pytest.mark.asyncio
    async def test_bulk_index_empty_ids(self, mock_outbox_service):
        """Test bulk index with empty IDs list."""
        mock_outbox_service.bulk_index = AsyncMock(
            return_value={"success": 0, "failed": 0, "total": 0}
        )

        with patch("app.background.tasks.outbox_task_service", mock_outbox_service):
            with patch(
                "app.background.tasks.run_async",
                AsyncMock(return_value={"success": 0, "failed": 0, "total": 0}),
            ):
                from app.background import tasks

                result = await tasks.bulk_index_async("task", ids=[])

                assert result.get("total") == 0

    @pytest.mark.asyncio
    async def test_bulk_index_invalid_model(self, mock_outbox_service):
        """Test bulk index with invalid model returns error."""
        mock_outbox_service.bulk_index = AsyncMock(
            return_value={"error": "Unknown model: invalid"}
        )

        with patch("app.background.tasks.outbox_task_service", mock_outbox_service):
            with patch(
                "app.background.tasks.run_async",
                AsyncMock(return_value={"error": "Unknown model: invalid"}),
            ):
                from app.background import tasks

                result = await tasks.bulk_index_async("invalid")

                assert result.get("error") is not None

    @pytest.mark.asyncio
    async def test_bulk_index_all_models(self, mock_outbox_service):
        """Test bulk index with all valid models."""
        models = ["task", "user", "group", "comment"]

        for model in models:
            mock_outbox_service.bulk_index = AsyncMock(
                return_value={"success": 1, "failed": 0, "total": 1}
            )

            with patch("app.background.tasks.outbox_task_service", mock_outbox_service):
                with patch(
                    "app.background.tasks.run_async",
                    AsyncMock(return_value={"success": 1, "failed": 0, "total": 1}),
                ):
                    from app.background import tasks

                    result = await tasks.bulk_index_async(model)

                    assert "success" in result


class TestProcessOutboxAsync:
    """Unit tests for process_outbox_async Celery task."""

    @pytest.fixture
    def mock_outbox_service(self):
        mock = MagicMock()
        mock.process_outbox = AsyncMock(return_value={"processed": 0})
        return mock

    @pytest.mark.asyncio
    async def test_process_empty_outbox(self, mock_outbox_service):
        """Test processing empty outbox returns zero."""
        mock_outbox_service.process_outbox = AsyncMock(return_value={"processed": 0})

        with patch("app.background.tasks.outbox_task_service", mock_outbox_service):
            with patch(
                "app.background.tasks.run_async",
                AsyncMock(return_value={"processed": 0}),
            ):
                from app.background import tasks

                result = await tasks.process_outbox_async(batch_size=100)

                assert result.get("processed") == 0

    @pytest.mark.asyncio
    async def test_process_with_events(self, mock_outbox_service):
        """Test processing outbox with events."""
        mock_outbox_service.process_outbox = AsyncMock(return_value={"processed": 5})

        with patch("app.background.tasks.outbox_task_service", mock_outbox_service):
            with patch(
                "app.background.tasks.run_async",
                AsyncMock(return_value={"processed": 5}),
            ):
                from app.background import tasks

                result = await tasks.process_outbox_async()

                assert result.get("processed") == 5

    @pytest.mark.asyncio
    async def test_process_batch_size(self, mock_outbox_service):
        """Test processing with custom batch size."""
        mock_outbox_service.process_outbox = AsyncMock(return_value={"processed": 0})

        with patch("app.background.tasks.outbox_task_service", mock_outbox_service):
            with patch(
                "app.background.tasks.run_async",
                AsyncMock(return_value={"processed": 0}),
            ):
                from app.background import tasks

                await tasks.process_outbox_async(batch_size=50)

    @pytest.mark.asyncio
    async def test_process_default_batch_size(self, mock_outbox_service):
        """Test processing with default batch size."""
        mock_outbox_service.process_outbox = AsyncMock(return_value={"processed": 0})

        with patch("app.background.tasks.outbox_task_service", mock_outbox_service):
            with patch(
                "app.background.tasks.run_async",
                AsyncMock(return_value={"processed": 0}),
            ):
                from app.background import tasks

                await tasks.process_outbox_async()

    @pytest.mark.asyncio
    async def test_process_result_structure(self, mock_outbox_service):
        """Test processing result structure."""
        mock_outbox_service.process_outbox = AsyncMock(return_value={"processed": 10})

        with patch("app.background.tasks.outbox_task_service", mock_outbox_service):
            with patch(
                "app.background.tasks.run_async",
                AsyncMock(return_value={"processed": 10}),
            ):
                from app.background import tasks

                result = await tasks.process_outbox_async()

                assert "processed" in result


class TestRetryFailedOutboxAsync:
    """Unit tests for retry_failed_outbox_async Celery task."""

    @pytest.fixture
    def mock_outbox_service(self):
        mock = MagicMock()
        mock.retry_failed_outbox = AsyncMock(return_value={"retried": 0})
        return mock

    @pytest.mark.asyncio
    async def test_retry_none_failed(self, mock_outbox_service):
        """Test retry with no failed events."""
        mock_outbox_service.retry_failed_outbox = AsyncMock(return_value={"retried": 0})

        with patch("app.background.tasks.outbox_task_service", mock_outbox_service):
            with patch(
                "app.background.tasks.run_async",
                AsyncMock(return_value={"retried": 0}),
            ):
                from app.background import tasks

                result = await tasks.retry_failed_outbox_async(max_retries=3)

                assert result.get("retried") == 0

    @pytest.mark.asyncio
    async def test_retry_with_failed(self, mock_outbox_service):
        """Test retry with failed events."""
        mock_outbox_service.retry_failed_outbox = AsyncMock(return_value={"retried": 5})

        with patch("app.background.tasks.outbox_task_service", mock_outbox_service):
            with patch(
                "app.background.tasks.run_async",
                AsyncMock(return_value={"retried": 5}),
            ):
                from app.background import tasks

                result = await tasks.retry_failed_outbox_async()

                assert result.get("retried") == 5

    @pytest.mark.asyncio
    async def test_retry_max_retries(self, mock_outbox_service):
        """Test retry with custom max_retries."""
        mock_outbox_service.retry_failed_outbox = AsyncMock(return_value={"retried": 0})

        with patch("app.background.tasks.outbox_task_service", mock_outbox_service):
            with patch(
                "app.background.tasks.run_async",
                AsyncMock(return_value={"retried": 0}),
            ):
                from app.background import tasks

                await tasks.retry_failed_outbox_async(max_retries=5)

    @pytest.mark.asyncio
    async def test_retry_default_max_retries(self, mock_outbox_service):
        """Test retry with default max_retries."""
        mock_outbox_service.retry_failed_outbox = AsyncMock(return_value={"retried": 0})

        with patch("app.background.tasks.outbox_task_service", mock_outbox_service):
            with patch(
                "app.background.tasks.run_async",
                AsyncMock(return_value={"retried": 0}),
            ):
                from app.background import tasks

                await tasks.retry_failed_outbox_async()

    @pytest.mark.asyncio
    async def test_retry_result_structure(self, mock_outbox_service):
        """Test retry result structure."""
        mock_outbox_service.retry_failed_outbox = AsyncMock(
            return_value={"retried": 10}
        )

        with patch("app.background.tasks.outbox_task_service", mock_outbox_service):
            with patch(
                "app.background.tasks.run_async",
                AsyncMock(return_value={"retried": 10}),
            ):
                from app.background import tasks

                result = await tasks.retry_failed_outbox_async()

                assert "retried" in result
