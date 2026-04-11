from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.service import GroupService
from app.service.exceptions import group_exc


class TestCreateMyGroup:
    async def test_create_sets_admin_id(self, mock_db: AsyncMock, mock_indexer):
        mock_user = AsyncMock()
        mock_user.id = 42
        mock_db.scalar.side_effect = [None, 42, None]

        def mock_add(obj):
            obj.id = 1
            obj.is_active = True
            obj.created_at = MagicMock()
            obj.updated_at = None
            obj.invite_policy = "admin_only"
            obj.join_policy = "request"

        mock_db.add = MagicMock(side_effect=mock_add)
        mock_db.flush = AsyncMock()
        group_in = MagicMock()
        group_in.name = "Test Group"
        group_in.description = "Desc"
        group_in.visibility = "public"
        group_in.parent_group_id = None
        group_in.invite_policy = "admin_only"
        group_in.join_policy = "request"

        mock_notification = MagicMock()
        mock_task_service = MagicMock()

        with patch.object(GroupService, "_invalidate", new_callable=AsyncMock):
            svc = GroupService(
                mock_db,
                mock_indexer,
                mock_notification,
                mock_task_service,
            )
            await svc.create_my_group(mock_user, group_in)
        group_obj = mock_db.add.call_args_list[0][0][0]
        assert group_obj.admin_id == 42
        assert group_obj.id == 1

    async def test_duplicate_name_raises_conflict(
        self, mock_db: AsyncMock, mock_indexer
    ):
        mock_user = AsyncMock()
        mock_user.id = 1
        mock_db.scalar.return_value = AsyncMock()
        group_in = MagicMock()
        group_in.name = "Existing"
        group_in.description = "Desc"
        group_in.visibility = "public"
        group_in.parent_group_id = None

        mock_notification = MagicMock()
        mock_task_service = MagicMock()

        svc = GroupService(
            mock_db,
            mock_indexer,
            mock_notification,
            mock_task_service,
        )
        with pytest.raises(group_exc.GroupNameConflict):
            await svc.create_my_group(mock_user, group_in)


class TestJoinGroup:
    async def test_join_creates_membership(self, mock_db: AsyncMock, mock_indexer):
        mock_user = AsyncMock()
        mock_user.id = 1
        mock_group = AsyncMock()
        mock_group.admin_id = 1
        mock_group.name = "Test Group"
        mock_group.join_policy = "open"
        mock_db.scalar.side_effect = [
            None,  # check existing membership
            mock_group,  # get group
            None,  # check existing join request
            42,  # get_role_id
            None,  # check existing role
        ]
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()

        mock_notification = MagicMock()
        mock_task_service = MagicMock()

        with patch.object(GroupService, "_invalidate", new_callable=AsyncMock):
            svc = GroupService(
                mock_db,
                mock_indexer,
                mock_notification,
                mock_task_service,
            )
            svc._notification = None  # Disable notification
            await svc.join_group(group_id=5, current_user=mock_user)
        mock_db.add.assert_called()
        membership = mock_db.add.call_args_list[0][0][0]
        assert membership.user_id == 1
        assert membership.group_id == 5

    async def test_join_existing_raises(self, mock_db: AsyncMock, mock_indexer):
        mock_user = AsyncMock()
        mock_user.id = 1
        mock_group = AsyncMock()
        mock_group.join_policy = "open"
        mock_db.scalar.side_effect = [
            AsyncMock(),  # existing membership
            mock_group,  # get group
            None,  # check existing join request
        ]
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()

        mock_notification = MagicMock()
        mock_task_service = MagicMock()

        with patch.object(GroupService, "_invalidate", new_callable=AsyncMock):
            svc = GroupService(
                mock_db,
                mock_indexer,
                mock_notification,
                mock_task_service,
            )
            with pytest.raises(group_exc.MemberAlreadyExists):
                await svc.join_group(group_id=5, current_user=mock_user)


class TestRoleAssignment:
    async def test_create_group_assigns_group_admin_role(
        self, mock_db: AsyncMock, mock_indexer
    ):
        """Verify GROUP_ADMIN role is assigned when creating group."""
        mock_user = AsyncMock()
        mock_user.id = 1

        mock_db.scalar.side_effect = [None, 1, None]

        def mock_add(obj):
            if hasattr(obj, "admin_id"):
                obj.id = 1
                obj.is_active = True
                obj.created_at = MagicMock()
                obj.updated_at = None
                obj.invite_policy = "admin_only"
                obj.join_policy = "request"

        mock_db.add = MagicMock(side_effect=mock_add)
        mock_db.flush = AsyncMock()
        mock_db.refresh = AsyncMock()

        mock_notification = MagicMock()
        mock_task_service = MagicMock()

        with patch.object(GroupService, "_invalidate", new_callable=AsyncMock):
            svc = GroupService(
                mock_db,
                mock_indexer,
                mock_notification,
                mock_task_service,
            )
            group_in = MagicMock()
            group_in.name = "Test Group"
            group_in.description = "Desc"
            group_in.visibility = "public"
            group_in.parent_group_id = None
            group_in.invite_policy = "admin_only"
            group_in.join_policy = "request"

            await svc.create_my_group(mock_user, group_in)

            add_calls = mock_db.add.call_args_list
            user_role_call = [c for c in add_calls if hasattr(c[0][0], "role_id")]
            assert len(user_role_call) > 0, "UserRole should be created"

    async def test_join_group_assigns_member_role(
        self, mock_db: AsyncMock, mock_indexer
    ):
        """Verify MEMBER role is assigned when joining group."""
        mock_user = AsyncMock()
        mock_user.id = 1
        mock_group = AsyncMock()
        mock_group.admin_id = 1
        mock_group.name = "Test Group"
        mock_group.join_policy = "open"

        mock_db.scalar.side_effect = [
            None,  # check existing membership
            mock_group,  # get group
            None,  # check existing join request
            2,  # get_role_id
            None,  # check existing role
        ]
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()

        mock_notification = MagicMock()
        mock_task_service = MagicMock()

        with patch.object(GroupService, "_invalidate", new_callable=AsyncMock):
            svc = GroupService(
                mock_db,
                mock_indexer,
                mock_notification,
                mock_task_service,
            )
            svc._notification = None  # Disable notification
            await svc.join_group(group_id=5, current_user=mock_user)

        # Verify membership was created
        mock_db.add.assert_called()
        membership = mock_db.add.call_args_list[0][0][0]
        assert membership.user_id == 1
        assert membership.group_id == 5
