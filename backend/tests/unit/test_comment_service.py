from unittest.mock import AsyncMock, MagicMock

import pytest

from app.service.comment import CommentService
from app.service.exceptions import comment_exc, task_exc


class TestCreateComment:
    async def test_create_comment_nonexistent_task_raises(
        self, mock_db: AsyncMock, mock_indexer
    ):
        mock_db.scalar.return_value = None
        mock_user = MagicMock()
        mock_user.id = 1

        svc = CommentService(mock_db, mock_indexer)
        with pytest.raises(task_exc.TaskNotFound):
            await svc.create_comment(
                task_id=999,
                content="Test",
                current_user=mock_user,
            )

    async def test_create_comment_with_invalid_parent_raises(
        self, mock_db: AsyncMock, mock_indexer
    ):
        mock_task = MagicMock()
        mock_task.id = 1

        mock_db.scalar.side_effect = [mock_task, None]
        mock_user = MagicMock()
        mock_user.id = 1

        svc = CommentService(mock_db, mock_indexer)
        with pytest.raises(comment_exc.NotFoundParentError):
            await svc.create_comment(
                task_id=1,
                content="Test",
                current_user=mock_user,
                parent_id=999,
            )


class TestGetComment:
    async def test_get_comment_not_found_raises(self, mock_db: AsyncMock, mock_indexer):
        mock_db.scalar.return_value = None

        svc = CommentService(mock_db, mock_indexer)
        with pytest.raises(comment_exc.CommentNotFoundError):
            await svc.get_comment(comment_id=999)


class TestUpdateComment:
    async def test_update_comment_not_owner_raises(
        self, mock_db: AsyncMock, mock_indexer
    ):
        mock_comment = MagicMock()
        mock_comment.id = 1
        mock_comment.user_id = 1

        mock_db.scalar.return_value = mock_comment

        mock_user = MagicMock()
        mock_user.id = 2
        mock_user.global_role = None

        svc = CommentService(mock_db, mock_indexer)
        with pytest.raises(comment_exc.ForbiddenError):
            await svc.update_comment(
                comment_id=1,
                content="New content",
                current_user=mock_user,
            )


class TestDeleteComment:
    async def test_delete_comment_not_owner_raises(
        self, mock_db: AsyncMock, mock_indexer
    ):
        mock_comment = MagicMock()
        mock_comment.id = 1
        mock_comment.user_id = 1

        mock_db.scalar.return_value = mock_comment

        mock_user = MagicMock()
        mock_user.id = 2
        mock_user.global_role = None

        svc = CommentService(mock_db, mock_indexer)
        with pytest.raises(comment_exc.ForbiddenError):
            await svc.delete_comment(comment_id=1, current_user=mock_user)
