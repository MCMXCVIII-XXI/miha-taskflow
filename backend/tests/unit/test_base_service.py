from unittest.mock import AsyncMock

import pytest

from app.service.base import GroupTaskBaseService
from app.service.exceptions import group_exc


class TestGetRoleId:
    """Group of tests for _get_role_id."""

    async def test_returns_role_id_when_found(self, mock_db: AsyncMock):
        """Checks that method returns id when role is found."""
        mock_db.scalar.return_value = 42
        service = GroupTaskBaseService(mock_db)
        result = await service._get_role_id("MEMBER")
        assert result == 42
        mock_db.scalar.assert_awaited_once()

    async def test_returns_none_when_role_not_found(self, mock_db: AsyncMock):
        """Checks that method returns None if role is not found."""
        mock_db.scalar.return_value = None
        service = GroupTaskBaseService(mock_db)
        result = await service._get_role_id("MEMBER")
        assert result is None


class TestBuildQueryForUserRole:
    """Group of tests for _build_query_for_user_role."""

    async def test_with_group_id_filters_by_group(self, mock_db: AsyncMock):
        """Checks that filter is by group_id when group_id is provided."""
        service = GroupTaskBaseService(mock_db)
        query = await service._build_query_for_user_role(
            group_id=5, task_id=None, user_id=1, role_id=2
        )
        assert query is not None

    async def test_without_group_id_and_task_id_raises(self, mock_db: AsyncMock):
        """Checks that without group_id and task_id raises ValueError."""
        service = GroupTaskBaseService(mock_db)
        with pytest.raises(group_exc.GroupMissingContextIdError):
            await service._build_query_for_user_role(
                group_id=None, task_id=None, user_id=1, role_id=2
            )


class TestGrantRoleIfNotExists:
    """Group of tests for _grant_role_if_not_exists."""

    async def test_creates_role_when_not_exists(self, mock_db: AsyncMock):
        """Checks that creates UserRole when role does not exist."""
        mock_db.scalar.side_effect = [42, None]
        service = GroupTaskBaseService(mock_db)
        await service._grant_role_if_not_exists(
            user_id=1, role_name="MEMBER", group_id=5
        )
        mock_db.add.assert_called_once()

    async def test_skips_when_role_exists(self, mock_db: AsyncMock):
        """Checks that does not create duplicate when role already exists."""
        mock_existing = AsyncMock()
        mock_db.scalar.side_effect = [42, mock_existing]
        service = GroupTaskBaseService(mock_db)
        await service._grant_role_if_not_exists(
            user_id=1, role_name="MEMBER", group_id=5
        )
        mock_db.add.assert_not_called()
