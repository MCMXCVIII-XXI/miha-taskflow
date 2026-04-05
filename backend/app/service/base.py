"""
================================
Base Management Service Module
================================

Module Description
=================
Base service class for all domain-specific services. Provides shared infrastructure
for database operations and cache management across all service implementations.

Module Components
=================
- BaseService: Abstract foundation for all services
  * AsyncSession injection and lifecycle management
  * FastAPICache namespace invalidation utilities
  * Standardized error handling patterns

Dependencies
============
- SQLAlchemy 2.x (AsyncSession for async ORM operations)
- fastapi-cache (namespace-based cache invalidation)
- FastAPI (dependency injection integration)

Usage
=====
```python
from app.services.base import BaseService
from app._db import _db_helper

class UserService(BaseService):
    async def some_operation(self):
        await self._invalidate("users")  # Clear user cache
        result = await self._db.scalars(...)
        return result.all()

@app.get("/users/")
async def get_users(db: AsyncSession = Depends(_db_helper.get_session)):
    user_svc = UserService(db)
    return await user_svc.some_operation()

Version History
v1.0.0 (2026-03-20)

    Initial release with AsyncSession injection

    FastAPICache namespace invalidation support

    Standardized service initialization pattern

v1.1.0 (Upcoming)

    Distributed cache support (Redis clustering)

    Automatic cache invalidation by model change

    Health checks and metrics integration

"""

from typing import Any, Literal

from fastapi_cache import FastAPICache
from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import rbac_exc
from app.models import Role as RoleModel
from app.models import UserRole as UserRoleModel
from app.schemas.enum import BaseRank, TaskSphere, XPThreshold, TaskDifficulty
from app.schemas.enum import SecondaryUserRole as SecondaryUserRoleEnum
from app.service.utils import StatsGroups, StatsTasks, StatsUsers

from .exceptions import group_exc


class BaseService:
    """
    Base service class for all domain services.

    Provides:
        - Database session via self._db
        - Cache namespace invalidation via FastAPICache singleton

    Attributes:
        _db (AsyncSession): SQLAlchemy async session for DB operations.
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def _invalidate(self, namespace: str) -> None:
        """
        Invalidate all cached entries under the given namespace.

        Arguments:
            namespace (str): Cache namespace to clear.
        """
        await FastAPICache.clear(namespace=namespace)


class GroupTaskBaseService(BaseService):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db)
        self._role = SecondaryUserRoleEnum

    async def _get_role_id(
        self, role_name: Literal["MEMBER", "GROUP_ADMIN", "ASSIGNEE"]
    ) -> int | None:
        if role_name == self._role.MEMBER.value:
            return await self._db.scalar(
                select(RoleModel.id).where(RoleModel.name == self._role.MEMBER.value)
            )
        elif role_name == self._role.GROUP_ADMIN.value:
            return await self._db.scalar(
                select(RoleModel.id).where(
                    RoleModel.name == self._role.GROUP_ADMIN.value
                )
            )
        elif role_name == self._role.ASSIGNEE.value:
            return await self._db.scalar(
                select(RoleModel.id).where(RoleModel.name == self._role.ASSIGNEE.value)
            )

    async def _build_query_for_user_role(
        self, group_id: int | None, task_id: int | None, user_id: int, role_id: int
    ) -> Select[tuple[UserRoleModel]]:
        query = select(UserRoleModel).where(
            UserRoleModel.user_id == user_id,
            UserRoleModel.role_id == role_id,
        )
        if group_id is not None:
            return query.where(UserRoleModel.group_id == group_id)
        elif task_id is not None:
            return query.where(UserRoleModel.task_id == task_id)
        else:
            raise group_exc.GroupMissingContextIdError(
                message="You must pass the group_id or task_id."
            )

    async def _grant_role_if_not_exists(
        self,
        user_id: int,
        role_name: Literal["MEMBER", "ASSIGNEE", "GROUP_ADMIN"],
        group_id: int | None = None,
        task_id: int | None = None,
    ) -> None:
        role_id = await self._get_role_id(role_name)

        if not role_id:
            raise rbac_exc.RoleNotFound(message=f"Role {role_name} not found")
        query = await self._build_query_for_user_role(
            group_id=group_id, task_id=task_id, user_id=user_id, role_id=role_id
        )
        existing = await self._db.scalar(query)

        if not existing:
            user_role = UserRoleModel(
                user_id=user_id, role_id=role_id, group_id=group_id, task_id=task_id
            )
            self._db.add(user_role)


class AdminBaseService(BaseService):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db)
        self._stats_users = StatsUsers(db)
        self._stats_groups = StatsGroups(db)
        self._stats_tasks = StatsTasks(db)

    async def _get_data(
        self,
        stat_users: bool = False,
        stat_groups: bool = False,
        stat_tasks: bool = False,
    ) -> dict[str, Any]:
        stats: dict[str, Any] = {"users": {}, "groups": {}, "tasks": {}}

        if stat_users:
            stats["users"] = await self._stats_users.get_stats() or {}
        if stat_groups:
            stats["groups"] = await self._stats_groups.get_stats() or {}
        if stat_tasks:
            stats["tasks"] = await self._stats_tasks.get_stats() or {}

        return stats


class XPBaseService(BaseService):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db)
        self._spheres = TaskSphere
        self._base_rank = BaseRank
        self._xp_thresholds = XPThreshold
        self._task_difficulty = TaskDifficulty
        self._max_daily_xp = 500
        self._frozen_days = 60

    def _get_xp_thresholds(self) -> dict[int, int]:
        data_xp_level: dict[int, int] = {}
        for indx, xp in enumerate(self._xp_thresholds):
            level = indx + 1
            data_xp_level.setdefault(level, xp.value)
        return data_xp_level

    def _get_levels_all_rank(self) -> list[type[BaseRank]]:
        return BaseRank.__subclasses__()

    def _get_sphere_titles(self) -> dict[str, dict[int, str]]:
        data_spheres = {}
        ranks = self._get_levels_all_rank()
        for sphere, rank_class in zip(self._spheres, ranks, strict=True):
            data_spheres[sphere.value] = {rank.level: rank.title for rank in rank_class}
        return data_spheres
