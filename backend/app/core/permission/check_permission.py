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
    """
    Get user permissions from database
    """
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
    return set(result.all())


def require_permissions_db(*required_permissions: str) -> Callable[..., Any]:
    """
    Check if user has required permissions

    Args:
        required_permissions (list[str]): List of required permissions

    Details:
        This function checks if the user has the required permissions.
        If the user does not have the required permissions,
        it raises a SecurityPermissionDenied exception.
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
