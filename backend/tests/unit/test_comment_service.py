from unittest.mock import AsyncMock, MagicMock

import pytest

from app.service.comment import CommentService
from app.service.exceptions import comment_exc, task_exc


@pytest.fixture
def mock_comment_transaction():
    mock = MagicMock()
    mock.create_comment = AsyncMock()
    mock.update_comment = AsyncMock()
    mock.delete_comment = AsyncMock()
    mock.get_comment = AsyncMock()
    return mock


class TestCreateComment:
    async def test_create_comment_nonexistent_task_raises(
        self, mock_db: AsyncMock, mock_indexer, mock_comment_transaction
    ):
        mock_comment_transaction.create_comment = AsyncMock(
            side_effect=task_exc.TaskNotFound(message="Task not found")
        )

        mock_user = MagicMock()
        mock_user.id = 1

        svc = CommentService(
            mock_db, mock_indexer, comment_transaction=mock_comment_transaction
        )
        with pytest.raises(task_exc.TaskNotFound):
            await svc.create_comment(
                task_id=999,
                content="Test",
                current_user=mock_user,
            )

    async def test_create_comment_with_invalid_parent_raises(
        self, mock_db: AsyncMock, mock_indexer, mock_comment_transaction
    ):
        mock_comment_transaction.create_comment = AsyncMock(
            side_effect=comment_exc.NotFoundParentError(message="Parent not found")
        )

        mock_user = MagicMock()
        mock_user.id = 1

        svc = CommentService(
            mock_db, mock_indexer, comment_transaction=mock_comment_transaction
        )
        with pytest.raises(comment_exc.NotFoundParentError):
            await svc.create_comment(
                task_id=1,
                content="Test",
                current_user=mock_user,
                parent_id=999,
            )


class TestGetComment:
    async def test_get_comment_not_found_raises(
        self, mock_db: AsyncMock, mock_indexer, mock_comment_transaction
    ):
        svc = CommentService(
            mock_db, mock_indexer, comment_transaction=mock_comment_transaction
        )
        svc._comment_repo = MagicMock()
        svc._comment_repo.get = AsyncMock(
            side_effect=comment_exc.CommentNotFoundError(message="Comment not found")
        )

        with pytest.raises(comment_exc.CommentNotFoundError):
            await svc.get_comment(comment_id=999)


class TestUpdateComment:
    async def test_update_comment_not_owner_raises(
        self, mock_db: AsyncMock, mock_indexer, mock_comment_transaction
    ):
        mock_comment_transaction.update_comment = AsyncMock(
            side_effect=comment_exc.ForbiddenError(message="Not owner")
        )

        mock_user = MagicMock()
        mock_user.id = 2

        svc = CommentService(
            mock_db, mock_indexer, comment_transaction=mock_comment_transaction
        )
        with pytest.raises(comment_exc.ForbiddenError):
            await svc.update_comment(
                comment_id=1,
                content="New content",
                current_user=mock_user,
            )


class TestDeleteComment:
    async def test_delete_comment_not_owner_raises(
        self, mock_db: AsyncMock, mock_indexer, mock_comment_transaction
    ):
        mock_comment_transaction.delete_comment = AsyncMock(
            side_effect=comment_exc.ForbiddenError(message="Not owner")
        )

        mock_user = MagicMock()
        mock_user.id = 2

        svc = CommentService(
            mock_db, mock_indexer, comment_transaction=mock_comment_transaction
        )
        with pytest.raises(comment_exc.ForbiddenError):
            await svc.delete_comment(comment_id=1, current_user=mock_user)
