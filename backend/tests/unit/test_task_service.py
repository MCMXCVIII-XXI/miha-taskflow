from unittest.mock import AsyncMock, MagicMock

import pytest

from app.service.exceptions import task_exc
from app.service.task import TaskService


class TestJoinTask:
    async def test_join_creates_assignee(self, mock_db: AsyncMock):
        mock_user = AsyncMock()
        mock_user.id = 1
        mock_db.scalar.side_effect = [
            None,
            42,
            None,
        ]  # check existing, get_role_id, check existing role
        svc = TaskService(mock_db)
        await svc.join_task(task_id=10, current_user=mock_user)
        mock_db.add.assert_called()
        assignee = mock_db.add.call_args_list[0][0][0]
        assert assignee.user_id == 1
        assert assignee.task_id == 10

    async def test_join_existing_raises(self, mock_db: AsyncMock):
        mock_user = AsyncMock()
        mock_user.id = 1
        mock_db.scalar.return_value = AsyncMock()
        svc = TaskService(mock_db)
        with pytest.raises(task_exc.UserAlreadyInTask):
            await svc.join_task(task_id=10, current_user=mock_user)


class TestTaskRoleAssignment:
    async def test_join_task_assigns_assignee_role(self, mock_db: AsyncMock):
        """Verify ASSIGNEE role is assigned when joining task."""
        mock_user = AsyncMock()
        mock_user.id = 1

        mock_db.scalar.side_effect = [None, 3, None]
        mock_db.add = MagicMock()
        mock_db.flush = AsyncMock()

        svc = TaskService(mock_db)
        await svc.join_task(task_id=10, current_user=mock_user)

        add_calls = mock_db.add.call_args_list
        user_role_call = [c for c in add_calls if hasattr(c[0][0], "role_id")]
        assert len(user_role_call) > 0, "UserRole should be created for ASSIGNEE"
