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
from sqlalchemy.ext.asyncio import AsyncSession

from app.cache import KeyBuilder
from app.core.log import logging
from app.core.metrics import METRICS
from app.models import UserRole as UserRoleModel
from app.repositories import (
    CommentRepository,
    GroupMembershipRepository,
    GroupRepository,
    JoinRequestRepository,
    NotificationRepository,
    OutboxRepository,
    RatingRepository,
    RoleRepository,
    TaskAssigneeRepository,
    TaskRepository,
    UserRepository,
    UserRoleRepository,
    UserSkillRepository,
)
from app.schemas.enum import BaseRank, TaskDifficulty, TaskSphere, XPThreshold
from app.schemas.enum import SecondaryUserRole as SecondaryUserRoleEnum
from app.service.utils import StatsGroups, StatsTasks, StatsUsers

from .exceptions import group_exc

logger = logging.get_logger(__name__)


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
        # REPOSITORIES #################################################
        self._outbox_repo = OutboxRepository(self._db)
        self._comment_repo = CommentRepository(self._db)
        self._group_membership_repo = GroupMembershipRepository(self._db)
        self._group_repo = GroupRepository(self._db)
        self._join_repo = JoinRequestRepository(self._db)
        self._notification_repo = NotificationRepository(self._db)
        self._rating_repo = RatingRepository(self._db)
        self._role_repo = RoleRepository(self._db)
        self._task_assignee_repo = TaskAssigneeRepository(self._db)
        self._task_repo = TaskRepository(self._db)
        self._user_repo = UserRepository(self._db)
        self._user_role_repo = UserRoleRepository(self._db)
        self._user_skill_repo = UserSkillRepository(self._db)

        METRICS.SERVICE_INIT_TOTAL.labels(service_name=self.__class__.__name__).inc()

    async def _invalidate(self, namespace: str) -> None:
        """Invalidate cache with automatic namespace normalization.

        Clears cached data for a specific namespace using FastAPI Cache.
        Handles namespace normalization automatically to ensure consistent
        cache key generation.

        Args:
            namespace: Cache namespace to invalidate (e.g., "users", "tasks", "groups")
                Type: str

        Returns:
            None

        Raises:
            None

        Example:
            ```python
            await self._invalidate("users")  # Clear user cache
            await self._invalidate("tasks")  # Clear task cache
            ```
        """
        normalized_ns = KeyBuilder._normalize_namespace(namespace)
        METRICS.CACHE_INVALIDATIONS_TOTAL.labels(namespace=namespace).inc()
        await FastAPICache.clear(namespace=normalized_ns)


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

        Retrieves the internal database ID for a role based on its human-readable
        name. Used for role assignment and validation operations.

        Args:
            role_name: Name of the role to look up
                Type: Literal["MEMBER", "GROUP_ADMIN", "ASSIGNEE"]
                Values: "MEMBER" for group members, "GROUP_ADMIN" for administrators,
                    "ASSIGNEE" for task assignees

        Returns:
            int | None: Database ID of the role, or None if role not found

        Raises:
            None

        Example:
            ```python
            role_id = await self._get_role_id("MEMBER")
            # Returns: 1 (or whatever the DB ID is for MEMBER role)
            ```
        """
        if role_name == self._role.MEMBER.value:
            return await self._role_repo.get_id(name=self._role.MEMBER.value)
        elif role_name == self._role.GROUP_ADMIN.value:
            return await self._role_repo.get_id(name=self._role.GROUP_ADMIN.value)
        elif role_name == self._role.ASSIGNEE.value:
            return await self._role_repo.get_id(name=self._role.ASSIGNEE.value)

    async def _build_query_for_user_role(
        self, group_id: int | None, task_id: int | None, user_id: int, role_id: int
    ) -> UserRoleModel | None:
        """Check if user has specific role assignment.

        Queries the database to determine if a user already has a specific
        role assignment within a given context (group and/or task).

        Args:
            group_id: Group ID for group-specific roles
                Type: int | None
                Can be None for task-only roles
            task_id: Task ID for task-specific roles
                Type: int | None
                Can be None for group-only roles
            user_id: User ID to check role for
                Type: int
            role_id: Role ID to check
                Type: int

        Returns:
            UserRoleModel | None: User role record if exists, None otherwise

        Raises:
            group_exc.GroupMissingContextIdError:
                If neither group_id nor task_id provided

        Example:
            ```python
            user_role = await self._build_query_for_user_role(
                group_id=1,
                task_id=None,
                user_id=5,
                role_id=2
            )
            ```
        """
        if not group_id and not task_id:
            raise group_exc.GroupMissingContextIdError(
                message="You must pass the group_id or task_id."
            )
        return await self._user_role_repo.get(
            user_id=user_id,
            role_id=role_id,
            group_id=group_id,
            task_id=task_id,
        )


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

        Collects and returns statistics about users, groups, and/or tasks
        based on the requested parameters. Used by admin services to
        gather dashboard metrics.

        Args:
            stat_users: Whether to include user statistics
                Type: bool
                Defaults to False
            stat_groups: Whether to include group statistics
                Type: bool
                Defaults to False
            stat_tasks: Whether to include task statistics
                Type: bool
                Defaults to False

        Returns:
            dict[str, Any]: Dictionary containing requested statistics data
                Keys: "users", "groups", "tasks" (only included if requested)
                Each value is a dictionary of statistics for that entity type

        Raises:
            None

        Example:
            ```python
            stats = await self._get_data(stat_users=True, stat_groups=True)
            # Returns: {"users": {...}, "groups": {...}}
            ```
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

        Returns a mapping of level numbers to their XP thresholds.
        These thresholds determine when a user advances to the next level.

        Returns:
            dict[int, int]: Dictionary mapping level numbers (1-10) to XP thresholds

        Example:
            ```python
            thresholds = self._get_xp_thresholds()
            # Returns: {1: 0, 2: 100, 3: 250, 4: 500, ...}
            ```
        """
        data_xp_level: dict[int, int] = {}
        for indx, xp in enumerate(self._xp_thresholds):
            level = indx + 1
            data_xp_level.setdefault(level, xp.value)
        return data_xp_level

    def _get_levels_all_rank(self) -> list[type[BaseRank]]:
        """Get all rank level classes.

        Returns all rank classes that define titles for different levels
        within each sphere.

        Returns:
            list[type[BaseRank]]: List of all BaseRank subclasses

        Example:
            ```python
            ranks = self._get_levels_all_rank()
            # Returns: [<class DeveloperRank>, <class DesignerRank>, ...]
            ```
        """
        return BaseRank.__subclasses__()

    def _get_sphere_titles(self) -> dict[str, dict[int, str]]:
        """Get titles for each sphere at each level.

        Builds a mapping of spheres to their level titles. Each sphere
        has different titles for different levels.

        Returns:
            dict[str, dict[int, str]]:
                Dictionary mapping sphere names to level-title mappings

        Example:
            ```python
            titles = self._get_sphere_titles()
            # Returns: {"development": {1: "Novice", 2: "Apprentice", ...}, ...}
            ```
        """
        data_spheres = {}
        ranks = self._get_levels_all_rank()
        for sphere, rank_class in zip(self._spheres, ranks, strict=True):
            data_spheres[sphere.value] = {rank.level: rank.title for rank in rank_class}
        return data_spheres
