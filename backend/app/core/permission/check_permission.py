from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import db_helper
from app.models import Permission, Role, RolePermission
from app.models import UserRole as UserRoleModel
from app.schemas.user_schemas import UserRead

from ..exceptions import security_exc
from ..security.auth import get_current_user


async def get_user_permissions_db(user_id: int, db: AsyncSession) -> set[str]:
    """
    Get user permissions from database
    """
    result = await db.scalars(
        select(Permission.name)  # select all permissions from the database
        .join(
            RolePermission, Permission.id == RolePermission.permission_id
        )  # select all role permissions
        .join(Role, RolePermission.role_id == Role.id)  # select all roles
        .join(UserRoleModel, UserRoleModel.role_id == Role.id)  # select all user roles
        .where(UserRoleModel.user_id == user_id)  # filter by user id
    )
    return set(result.all())


def require_permissions_db(
    *required_permissions: str,
) -> Callable:  # type: ignore
    """
    Check if user has required permissions

    Args:
        required_permissions (list[str]): List of required permissions

        Args:
            current_user (UserSchema): Current user
            db (AsyncSession): Database session

    Details:
        This function checks if the user has the required permissions.
        If the user does not have the required permissions,
        it raises a SecurityPermissionDenied exception.
    """

    async def dependency(
        current_user: UserRead = Depends(get_current_user),
        db: AsyncSession = Depends(db_helper.get_session),
    ) -> UserRead:
        perms = await get_user_permissions_db(current_user.id, db)
        missing = [p for p in required_permissions if p not in perms]
        if missing:
            raise security_exc.SecurityPermissionDenied(
                message="You do not have permission to perform this action",
                details={"Missing": missing},
            )
        return current_user

    return dependency
