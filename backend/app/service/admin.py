"""Administrative service for system management and user administration.

This service provides administrative functionality for managing users,
monitoring system statistics, and performing administrative operations
that require elevated privileges.
"""

from typing import Any

from fastapi import Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.log import get_logger
from app.db import db_helper
from app.es import ElasticsearchIndexer, get_es_indexer
from app.models import User as UserModel
from app.schemas import (
    UserRead,
    UserSearch,
)
from app.schemas.enum import GlobalUserRole
from app.service.utils.get_stats import StatsGroups, StatsTasks, StatsUsers

from .base import BaseService
from .exceptions import user_exc
from .query_db import GroupQueries, UserQueries
from .utils import Indexer

logger = get_logger("service.admin")


class AdminService(BaseService):
    """Provides administrative functionality for system management.

    This service implements administrative operations including user management,
    system statistics collection, and administrative user operations.
    It requires elevated privileges and handles sensitive system operations.

    Attributes:
        user_queries (UserQueries): User query builder for database operations
        group_queries (GroupQueries): Group query builder for database operations
        _indexer (Indexer): Elasticsearch indexer for search integration
    """

    def __init__(self, db: AsyncSession, es: ElasticsearchIndexer) -> None:
        """Initialize administrative service with database and Elasticsearch.

        Args:
            db (AsyncSession): Database session for administrative operations
            es (ElasticsearchIndexer): Elasticsearch client for indexing operations
        """
        super().__init__(db)
        self.user_queries = UserQueries
        self.group_queries = GroupQueries
        self._indexer = Indexer(es)

    async def get_all_users(
        self,
        search: UserSearch | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[UserRead]:
        """Retrieve all users with optional search and pagination.

        Provides administrative access to all users in the system with filtering
        capabilities and pagination support for efficient data retrieval.

        Args:
            search (UserSearch | None): Search parameters for filtering users
            limit (int): Maximum number of users to return (default: 50)
            offset (int): Number of users to skip for pagination (default: 0)

        Returns:
            list[UserRead]: List of user profiles matching search criteria
        """
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
        """Delete a user account with administrative privileges.

        Performs soft-delete of user account with validation to prevent
        deletion of self or the last remaining admin user. Updates
        Elasticsearch index to reflect deletion.

        Args:
            user_id (int): ID of user to be deleted
            admin_id (int): ID of administrator performing the deletion

        Raises:
            user_exc.UserSelfDeleteError: When admin tries to delete themselves
            user_exc.UserNotFound: When target user does not exist
            user_exc.CannotDeleteLastAdmin: When trying to delete last admin user
        """
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
        await self._indexer.delete({"type": "user", "id": user.id})

        logger.info(
            "User deleted: user_id={user_id} by admin_id={admin_id}",
            user_id=user_id,
            admin_id=admin_id,
        )

    async def get_stats(self) -> dict[str, Any]:
        """Retrieve system statistics for administrative dashboard.

        Collects comprehensive statistics about users, groups, and tasks
        for system monitoring and administrative overview.

        Returns:
            dict[str, Any]: Dictionary containing system statistics by entity type
        """
        stats_users = StatsUsers(self._db)
        stats_groups = StatsGroups(self._db)
        stats_tasks = StatsTasks(self._db)

        return {
            "users": await stats_users.get_stats(),
            "groups": await stats_groups.get_stats(),
            "tasks": await stats_tasks.get_stats(),
        }


def get_admin_service(
    db: AsyncSession = Depends(db_helper.get_session),
    es: ElasticsearchIndexer = Depends(get_es_indexer),
) -> AdminService:
    """FastAPI dependency for AdminService instantiation.

    Creates and configures AdminService instance with required dependencies.

    Args:
        db (AsyncSession): Database session from dependency injection
        es (ElasticsearchIndexer): Elasticsearch client from dependency injection

    Returns:
        AdminService: Configured administrative service instance
    """
    return AdminService(db, es)
