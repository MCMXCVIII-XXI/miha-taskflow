from unittest.mock import AsyncMock, MagicMock

import pytest

from app.schemas import GlobalUserRole
from app.service.admin import AdminService
from app.service.exceptions import user_exc


class TestDeleteUser:
    async def test_delete_self_raises_error(self, mock_db: AsyncMock):
        """Test that admin cannot delete themselves."""
        svc = AdminService(mock_db)

        with pytest.raises(user_exc.UserSelfDeleteError):
            await svc.delete_user(user_id=1, admin_id=1)

    async def test_delete_nonexistent_raises_error(self, mock_db: AsyncMock):
        """Test that deleting nonexistent user raises error."""
        mock_db.get = AsyncMock(return_value=None)
        svc = AdminService(mock_db)

        with pytest.raises(user_exc.UserNotFound):
            await svc.delete_user(user_id=999, admin_id=1)

    async def test_delete_last_admin_raises_error(self, mock_db: AsyncMock):
        """Test that cannot delete the last admin."""
        mock_user = MagicMock()
        mock_user.role = GlobalUserRole.ADMIN

        mock_db.get = AsyncMock(return_value=mock_user)

        mock_result = MagicMock()
        mock_result.scalar.return_value = 1
        mock_db.execute = AsyncMock(return_value=mock_result)

        svc = AdminService(mock_db)

        with pytest.raises(user_exc.CannotDeleteLastAdmin):
            await svc.delete_user(user_id=2, admin_id=1)

    async def test_delete_regular_user_success(self, mock_db: AsyncMock):
        """Test successful deletion of regular user."""
        mock_user = MagicMock()
        mock_user.role = GlobalUserRole.USER

        mock_db.get = AsyncMock(return_value=mock_user)

        mock_result = MagicMock()
        mock_result.scalar.return_value = 0
        mock_db.execute = AsyncMock(return_value=mock_result)

        svc = AdminService(mock_db)

        await svc.delete_user(user_id=2, admin_id=1)

        assert mock_user.is_active == False  # noqa: E712
        mock_db.commit.assert_awaited_once()


class TestGetStats:
    async def test_get_stats_returns_dict_structure(self, mock_db: AsyncMock):
        """Test that get_stats returns dict with expected keys."""

        async def mock_scalar(query):
            mock_result = MagicMock()
            mock_result._mapping = {}
            return mock_result

        async def mock_execute(query):
            mock_result = MagicMock()
            mock_result._mapping = {
                "total": 10,
                "active": 8,
                "not_active": 2,
                "admins": 1,
            }
            return mock_result

        mock_db.scalar = AsyncMock(side_effect=mock_scalar)
        mock_db.execute = AsyncMock(side_effect=mock_execute)

        svc = AdminService(mock_db)

        result = await svc.get_stats()

        assert isinstance(result, dict)
        assert "users" in result
        assert "groups" in result
        assert "tasks" in result
