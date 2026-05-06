from unittest.mock import AsyncMock, MagicMock

import pytest

from app.schemas.enum import GlobalUserRole
from app.service.admin import AdminService
from app.service.exceptions import user_exc


class TestDeleteUser:
    async def test_delete_self_raises_error(
        self,
        mock_db: AsyncMock,
        mock_indexer,
    ):
        mock_transaction = MagicMock()
        mock_transaction.delete_user = AsyncMock()

        svc = AdminService(mock_db, mock_indexer, admin_transaction=mock_transaction)

        with pytest.raises(user_exc.UserSelfDeleteError):
            await svc.delete_user(user_id=1, admin_id=1)

    async def test_delete_nonexistent_raises_error(
        self,
        mock_db: AsyncMock,
        mock_indexer,
    ):
        mock_transaction = MagicMock()
        mock_transaction.delete_user = AsyncMock(
            side_effect=user_exc.UserNotFound(message="")
        )

        svc = AdminService(mock_db, mock_indexer, admin_transaction=mock_transaction)

        with pytest.raises(user_exc.UserNotFound):
            await svc.delete_user(user_id=999, admin_id=1)

    async def test_delete_last_admin_raises_error(
        self,
        mock_db: AsyncMock,
        mock_indexer,
    ):
        mock_transaction = MagicMock()
        mock_transaction.delete_user = AsyncMock(
            side_effect=user_exc.CannotDeleteLastAdmin(message="")
        )

        svc = AdminService(mock_db, mock_indexer, admin_transaction=mock_transaction)

        with pytest.raises(user_exc.CannotDeleteLastAdmin):
            await svc.delete_user(user_id=2, admin_id=1)

    async def test_delete_regular_user_success(
        self,
        mock_db: AsyncMock,
        mock_indexer,
    ):
        mock_user = MagicMock()
        mock_user.role = GlobalUserRole.USER
        mock_user.is_active = True

        mock_transaction = MagicMock()
        mock_transaction.delete_user = AsyncMock()

        svc = AdminService(mock_db, mock_indexer, admin_transaction=mock_transaction)

        await svc.delete_user(user_id=2, admin_id=1)

        mock_transaction.delete_user.assert_called_once()


class TestGetStats:
    async def test_get_stats_returns_dict_structure(
        self,
        mock_db: AsyncMock,
        mock_indexer,
    ):
        mock_user_result = MagicMock()
        mock_user_result.mappings.return_value.first.return_value = {
            "total": 10,
            "active": 8,
            "not_active": 2,
            "admins": 1,
        }

        mock_group_result = MagicMock()
        mock_group_result.mappings.return_value.first.return_value = {
            "total": 5,
            "active": 4,
            "not_active": 1,
        }

        mock_task_result = MagicMock()
        mock_task_result.mappings.return_value.first.return_value = {
            "total": 20,
            "active": 15,
            "not_active": 5,
        }

        mock_db.execute = AsyncMock(
            side_effect=[mock_user_result, mock_group_result, mock_task_result]
        )

        mock_transaction = MagicMock()
        svc = AdminService(mock_db, mock_indexer, admin_transaction=mock_transaction)

        result = await svc.get_stats()

        assert isinstance(result, dict)
        assert "users" in result
        assert "groups" in result
        assert "tasks" in result

        user_stats = result["users"]
        assert user_stats["total"] == 10
        assert user_stats["active"] == 8
        assert user_stats["not_active"] == 2
        assert user_stats["admins"] == 1
