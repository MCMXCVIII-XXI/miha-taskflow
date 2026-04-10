"""Permission checking utilities for Role-Based Access Control (RBAC).

This module implements the permission checking system for TaskFlow's RBAC.
It retrieves user permissions from the database and validates access
based on required permissions for specific operations.
"""

from collections.abc import Callable
from typing import Any

from fastapi import Depends
from sqlalchemy import String, func, select, union
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import security_exc
from app.core.security.auth import get_current_user
from app.db import db_helper
from app.models import Permission, Role, RolePermission
from app.models import User as UserModel
from app.models import UserRole as UserRoleModel


async def get_user_permissions_db(user_id: int, db: AsyncSession) -> set[str]:
    """Get user permissions from database."""
    global_query = (
        select(Permission.name)
        .join(RolePermission, Permission.id == RolePermission.permission_id)
        .join(Role, RolePermission.role_id == Role.id)
        .join(UserModel, func.cast(UserModel.role, String) == Role.name)
        .where(UserModel.id == user_id)
    )
    secondary_query = (
        select(Permission.name)
        .join(RolePermission, Permission.id == RolePermission.permission_id)
        .join(Role, RolePermission.role_id == Role.id)
        .join(UserRoleModel, UserRoleModel.role_id == Role.id)
        .where(UserRoleModel.user_id == user_id)
    )
    result = await db.scalars(union(global_query, secondary_query))
    perms = set(result.all())
    return perms


def require_permissions_db(*required_permissions: str) -> Callable[..., Any]:
    """Dependency factory for permission-based access control.

    Creates a FastAPI dependency that validates if the current user
    has all the required permissions to access an endpoint or perform
    an operation. Raises SecurityPermissionDenied if access is denied.

    Args:
        *required_permissions (str): Variable number of permission names
            that are required for access (e.g., "task:create:own")

    Returns:
        Callable[..., Any]: FastAPI dependency function

    Raises:
        security_exc.SecurityPermissionDenied: When user lacks required permissions

    Example:
        @router.get("/tasks")
        async def get_tasks(
            current_user: UserModel = Depends(require_permissions_db("task:view:any"))
        ):
            # Only users with "task:view:any" permission can access this
            pass
    """

    async def dependency(
        current_user: UserModel = Depends(get_current_user),
        db: AsyncSession = Depends(db_helper.get_session),
    ) -> UserModel:
        perms = await get_user_permissions_db(current_user.id, db)
        perms_set: set[str] = perms if isinstance(perms, set) else set()
        missing = [p for p in required_permissions if p not in perms_set]
        if missing:
            raise security_exc.SecurityPermissionDenied(
                message="You do not have permission to perform this action",
                details={"Missing": missing},
            )
        return current_user

    return dependency
