from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.exceptions import security_exc
from app.core.permission import check_permission, require_permissions_db


class TestRequirePermissionsDb:
    async def test_grants_access_when_permission_exists(self):
        """Allow access when user has required permission."""
        mock_user = MagicMock()
        mock_user.id = 1

        mock_db = AsyncMock()

        async def mock_get_permissions(user_id: int, db: AsyncMock):
            return {"group:create:own", "task:view:any"}

        original_get = check_permission.get_user_permissions_db
        check_permission.get_user_permissions_db = mock_get_permissions

        try:
            dependency = require_permissions_db("group:create:own")
            result = await dependency(current_user=mock_user, db=mock_db)
            assert result.id == 1
        finally:
            check_permission.get_user_permissions_db = original_get

    async def test_denies_access_when_permission_missing(self):
        """Deny access when user lacks required permission."""
        mock_user = MagicMock()
        mock_user.id = 1

        mock_db = AsyncMock()

        async def mock_get_permissions(user_id: int, db: AsyncMock):
            return {"task:view:any"}

        original_get = check_permission.get_user_permissions_db
        check_permission.get_user_permissions_db = mock_get_permissions

        try:
            dependency = require_permissions_db("group:create:own")
            with pytest.raises(security_exc.SecurityPermissionDenied):
                await dependency(current_user=mock_user, db=mock_db)
        finally:
            check_permission.get_user_permissions_db = original_get

    async def test_denies_access_when_no_permissions(self):
        """Deny access when user has no permissions."""
        mock_user = MagicMock()
        mock_user.id = 1

        mock_db = AsyncMock()

        async def mock_get_permissions(user_id: int, db: AsyncMock):
            return set()

        original_get = check_permission.get_user_permissions_db
        check_permission.get_user_permissions_db = mock_get_permissions

        try:
            dependency = require_permissions_db("group:create:own")
            with pytest.raises(security_exc.SecurityPermissionDenied):
                await dependency(current_user=mock_user, db=mock_db)
        finally:
            check_permission.get_user_permissions_db = original_get

    async def test_allows_when_has_all_required_permissions(self):
        """Allow access when user has all required permissions."""
        mock_user = MagicMock()
        mock_user.id = 1

        mock_db = AsyncMock()

        async def mock_get_permissions(user_id: int, db: AsyncMock):
            return {"group:create:own", "group:view:own", "task:create:own"}

        original_get = check_permission.get_user_permissions_db
        check_permission.get_user_permissions_db = mock_get_permissions

        try:
            dependency = require_permissions_db("group:create:own", "task:create:own")
            result = await dependency(current_user=mock_user, db=mock_db)
            assert result.id == 1
        finally:
            check_permission.get_user_permissions_db = original_get

    async def test_denies_when_missing_one_permission(self):
        """Deny access when missing one of multiple permissions."""
        mock_user = MagicMock()
        mock_user.id = 1

        mock_db = AsyncMock()

        async def mock_get_permissions(user_id: int, db: AsyncMock):
            return {"group:create:own"}

        original_get = check_permission.get_user_permissions_db
        check_permission.get_user_permissions_db = mock_get_permissions

        try:
            dependency = require_permissions_db("group:create:own", "task:delete:own")
            with pytest.raises(security_exc.SecurityPermissionDenied):
                await dependency(current_user=mock_user, db=mock_db)
        finally:
            check_permission.get_user_permissions_db = original_get

    async def test_allows_admin_permission(self):
        """Allow access when user has admin permission."""
        mock_user = MagicMock()
        mock_user.id = 1

        mock_db = AsyncMock()

        async def mock_get_permissions(user_id: int, db: AsyncMock):
            return {"admin:users:view", "admin:users:delete"}

        original_get = check_permission.get_user_permissions_db
        check_permission.get_user_permissions_db = mock_get_permissions

        try:
            dependency = require_permissions_db("admin:users:view")
            result = await dependency(current_user=mock_user, db=mock_db)
            assert result.id == 1
        finally:
            check_permission.get_user_permissions_db = original_get

    async def test_empty_permission_list(self):
        """Allow access when no permissions required."""
        mock_user = MagicMock()
        mock_user.id = 1

        mock_db = AsyncMock()

        async def mock_get_permissions(user_id: int, db: AsyncMock):
            return set()

        original_get = check_permission.get_user_permissions_db
        check_permission.get_user_permissions_db = mock_get_permissions

        try:
            dependency = require_permissions_db()
            result = await dependency(current_user=mock_user, db=mock_db)
            assert result.id == 1
        finally:
            check_permission.get_user_permissions_db = original_get
