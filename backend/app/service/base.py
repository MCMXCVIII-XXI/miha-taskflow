"""Base service classes for all domain-specific services.

This module provides base service classes that contain shared infrastructure
for database operations and cache management across all service implementations.
It also includes common functionality for role management and XP calculations.

The module contains:
- BaseService: Core base class with database session and cache invalidation
- GroupTaskBaseService: Base for services dealing with groups and tasks
- AdminBaseService: Base for administrative services with stats functionality
- XPBaseService: Base for services with XP and leveling functionality

Example:
    ```python
    from app.service.base import BaseService
    from app.db import db_helper

    class UserService(BaseService):
        async def some_operation(self):
            await self._invalidate("users")  # Clear user cache
            result = await self._db.scalars(...)
            return result.all()

    # Usage in FastAPI endpoint
    @app.get("/users/")
    async def get_users(db: AsyncSession = Depends(db_helper.get_session)):
        user_svc = UserService(db)
        return await user_svc.some_operation()
    ```
"""

from typing import Any, Literal

from fastapi_cache import FastAPICache
from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import rbac_exc
from app.models import Role as RoleModel
from app.models import UserRole as UserRoleModel
from app.schemas.enum import BaseRank, TaskDifficulty, TaskSphere, XPThreshold
from app.schemas.enum import SecondaryUserRole as SecondaryUserRoleEnum
from app.service.utils import StatsGroups, StatsTasks, StatsUsers

from .exceptions import group_exc


class BaseService:
    """Base service class for all domain services.

    Provides common functionality for all service classes including database
    session management and cache invalidation. This is the foundation for all
    domain-specific service classes.

    Attributes:
        _db (AsyncSession): SQLAlchemy async session for database operations
    """

    def __init__(self, db: AsyncSession) -> None:
        """Initialize base service with database session.

        Args:
            db: SQLAlchemy async session for database operations
        """
        self._db = db

    async def _invalidate(self, namespace: str, tags: list[str] | None = None) -> None:
        """Invalidate all cached entries under the given namespace and/or tags.

        Args:
            namespace: Cache namespace to clear
            tags: Optional list of tags to invalidate
        """
        await FastAPICache.clear(namespace=namespace)
        # TODO: Implement tag-based invalidation when FastAPI-Cache supports it
        # For now, we only support namespace invalidation
        if tags:
            # In a real implementation, we would invalidate by tags
            # This is a placeholder for future enhancement
            pass


class GroupTaskBaseService(BaseService):
    """Base service class for services dealing with groups and tasks.

    Provides common functionality for services that need to manage group
    memberships, task assignments, and related role management operations.

    Attributes:
        _db (AsyncSession): SQLAlchemy async session for database operations
        _role (SecondaryUserRoleEnum): Secondary user role enumeration
    """

    def __init__(self, db: AsyncSession) -> None:
        """Initialize GroupTaskBaseService with database session.

        Args:
            db: SQLAlchemy async session for database operations
        """
        super().__init__(db)
        self._role = SecondaryUserRoleEnum

    async def _get_role_id(
        self, role_name: Literal["MEMBER", "GROUP_ADMIN", "ASSIGNEE"]
    ) -> int | None:
        """Get the database ID for a role by name.

        Args:
            role_name: Name of the role to look up (MEMBER, GROUP_ADMIN, ASSIGNEE)

        Returns:
            int | None: Database ID of the role or None if not found
        """
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
        """Build SQLAlchemy query for checking user role assignments.

        Args:
            group_id: Group ID for group-specific roles (can be None)
            task_id: Task ID for task-specific roles (can be None)
            user_id: User ID to check role for
            role_id: Role ID to check

        Returns:
            Select[tuple[UserRoleModel]]: SQLAlchemy query for role checking

        Raises:
            group_exc.GroupMissingContextIdError:
                If neither group_id nor task_id provided
        """
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
        """Grant a role to a user if they don't already have it.

        Args:
            user_id: ID of user to grant role to
            role_name: Name of role to grant (MEMBER, ASSIGNEE, GROUP_ADMIN)
            group_id: Optional group ID for group-specific roles
            task_id: Optional task ID for task-specific roles

        Raises:
            rbac_exc.RoleNotFound: If the role doesn't exist in the database
            group_exc.GroupMissingContextIdError:
                If neither group_id nor task_id provided
        """
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
    """Base service class for administrative services with statistics functionality.

    Provides common functionality for administrative services that need to gather
    and process system statistics about users, groups, and tasks.

    Attributes:
        _db (AsyncSession): SQLAlchemy async session for database operations
        _stats_users (StatsUsers): User statistics utility
        _stats_groups (StatsGroups): Group statistics utility
        _stats_tasks (StatsTasks): Task statistics utility
    """

    def __init__(self, db: AsyncSession) -> None:
        """Initialize AdminBaseService with database session and stats utilities.

        Args:
            db: SQLAlchemy async session for database operations
        """
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
        """Get system statistics data.

        Collects statistics about users, groups,
            and tasks based on requested parameters.

        Args:
            stat_users: Whether to include user statistics
            stat_groups: Whether to include group statistics
            stat_tasks: Whether to include task statistics

        Returns:
            dict[str, Any]: Dictionary containing requested statistics data
        """
        stats: dict[str, Any] = {"users": {}, "groups": {}, "tasks": {}}

        if stat_users:
            stats["users"] = await self._stats_users.get_stats() or {}
        if stat_groups:
            stats["groups"] = await self._stats_groups.get_stats() or {}
        if stat_tasks:
            stats["tasks"] = await self._stats_tasks.get_stats() or {}

        return stats


class XPBaseService(BaseService):
    """Base service class for services with XP and leveling functionality.

    Provides common functionality for services that need to calculate XP,
    manage user levels, and handle task difficulty-based rewards.

    Attributes:
        _db (AsyncSession): SQLAlchemy async session for database operations
        _spheres (TaskSphere): Task sphere enumeration
        _base_rank (BaseRank): Base rank enumeration
        _xp_thresholds (XPThreshold): XP threshold enumeration
        _task_difficulty (TaskDifficulty): Task difficulty enumeration
        _max_daily_xp (int): Maximum XP that can be earned per day (500)
        _frozen_days (int): Days after which XP is considered frozen (60)
    """

    def __init__(self, db: AsyncSession) -> None:
        """Initialize XPBaseService with database session and XP configurations.

        Args:
            db: SQLAlchemy async session for database operations
        """
        super().__init__(db)
        self._spheres = TaskSphere
        self._base_rank = BaseRank
        self._xp_thresholds = XPThreshold
        self._task_difficulty = TaskDifficulty
        self._max_daily_xp = 500
        self._frozen_days = 60

    def _get_xp_thresholds(self) -> dict[int, int]:
        """Get XP thresholds for each level.

        Returns:
            dict[int, int]: Dictionary mapping level numbers to XP thresholds
        """
        data_xp_level: dict[int, int] = {}
        for indx, xp in enumerate(self._xp_thresholds):
            level = indx + 1
            data_xp_level.setdefault(level, xp.value)
        return data_xp_level

    def _get_levels_all_rank(self) -> list[type[BaseRank]]:
        """Get all rank level classes.

        Returns:
            list[type[BaseRank]]: List of all rank level classes
        """
        return BaseRank.__subclasses__()

    def _get_sphere_titles(self) -> dict[str, dict[int, str]]:
        """Get titles for each sphere at each level.

        Returns:
            dict[str, dict[int, str]]: Dictionary mapping spheres to level titles
        """
        data_spheres = {}
        ranks = self._get_levels_all_rank()
        for sphere, rank_class in zip(self._spheres, ranks, strict=True):
            data_spheres[sphere.value] = {rank.level: rank.title for rank in rank_class}
        return data_spheres
