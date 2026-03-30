from typing import Any

from fastapi import Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.log import get_logger
from app.db import db_helper
from app.models import User as UserModel
from app.schemas import (
    GlobalUserRole,
    UserRead,
    UserSearch,
)

from .base import BaseService
from .exceptions import user_exc
from .query_db import GroupQueries, UserQueries

logger = get_logger("service.admin")


def get_admin_service(
    db: AsyncSession = Depends(db_helper.get_session),
) -> "AdminService":
    return AdminService(db)


class AdminService(BaseService):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db)
        self.user_queries = UserQueries
        self.group_queries = GroupQueries

    async def get_all_users(
        self,
        search: UserSearch | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[UserRead]:
        if search is None:
            search = UserSearch()
        query = select(UserModel).where(UserModel.is_active)

        if search.username:
            query = query.where(UserModel.username.ilike(f"%{search.username}%"))
        if search.email:
            query = query.where(UserModel.email.ilike(f"%{search.email}%"))
        if search.role:
            query = query.where(UserModel.role == search.role)

        query = query.limit(limit).offset(offset)
        result = await self._db.scalars(query)
        users = result.all()

        return [UserRead.model_validate(user) for user in users]

    async def delete_user(self, user_id: int, admin_id: int) -> None:
        if user_id == admin_id:
            logger.warning(
                "Admin {admin_id} tried to delete themselves",
                admin_id=admin_id,
            )
            raise user_exc.UserSelfDeleteError(message="Cannot delete yourself")

        user = await self._db.get(UserModel, user_id)
        if not user:
            raise user_exc.UserNotFound(message=f"User with id {user_id} not found")

        if user.role == GlobalUserRole.ADMIN:
            admin_count_result = await self._db.execute(
                select(func.count(UserModel.id)).where(
                    UserModel.role == GlobalUserRole.ADMIN,
                    UserModel.is_active,
                )
            )
            admin_count = admin_count_result.scalar()

            if admin_count and admin_count <= 1:
                logger.warning(
                    "Admin {admin_id} tried to delete last admin {user_id}",
                    admin_id=admin_id,
                    user_id=user_id,
                )
                raise user_exc.CannotDeleteLastAdmin(
                    message="Cannot delete the last admin"
                )

        user.is_active = False
        await self._db.commit()

        logger.info(
            "User deleted: user_id={user_id} by admin_id={admin_id}",
            user_id=user_id,
            admin_id=admin_id,
        )

    async def get_stats(self) -> dict[str, Any]:
        from app.service.utils.get_stats import StatsGroups, StatsTasks, StatsUsers

        stats_users = StatsUsers(self._db)
        stats_groups = StatsGroups(self._db)
        stats_tasks = StatsTasks(self._db)

        return {
            "users": await stats_users.get_stats(),
            "groups": await stats_groups.get_stats(),
            "tasks": await stats_tasks.get_stats(),
        }
