"""Administrative service for system management operations.

This module provides the AdminService class for handling administrative tasks
such as user management, statistics gathering, and system monitoring.

**Key Components:**
* `AdminService`: Main service class for administrative operations;
* `get_admin_service`: FastAPI dependency injection factory.

**Dependencies:**
* `UserRepository`: User data access layer;
* `UnitOfWork`: Transaction management;
* `ElasticsearchIndexer`: Search index management;
* `StatsUsers`, `StatsGroups`, `StatsTasks`: Statistics aggregation.

**Usage Example:**
    ```python
    from app.service.admin import get_admin_service

    @router.get("/admin/users")
    async def get_users(service: AdminService = Depends(get_admin_service)):
        return await service.get_all_users()
    ```

**Notes:**
- Requires GLOBAL_ADMIN role for most operations;
- Soft deletes users (sets is_active=False);
- Statistics are computed in real-time from database.
"""

from typing import Any

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.log import get_logger
from app.core.metrics import METRICS
from app.db import db_helper
from app.es import ElasticsearchIndexer, get_es_indexer
from app.repositories.dict import UserIlike
from app.schemas import (
    UserRead,
    UserSearch,
)
from app.service.utils.get_stats import StatsGroups, StatsTasks, StatsUsers

from .base import BaseService
from .exceptions import user_exc
from .transactions.admin import AdminTransaction, get_admin_transaction
from .utils import Indexer

logger = get_logger(__name__)


class AdminService(BaseService):
    """Service for administrative operations including user management and statistics.

    Provides functionality for system administrators to manage users, view
    system statistics, and perform bulk operations. All operations require
    appropriate admin privileges.

    Attributes:
        _db (AsyncSession): SQLAlchemy async session for database operations
        _user_repository (UserRepository): Repository for user data operations
        _indexer (Indexer): Elasticsearch indexer wrapper for search operations
        _uow (UnitOfWork): Unit of work for transaction management

    Example:
        ```python
        admin_service = AdminService(
            db=session,
            indexer=indexer,
            user_repository=user_repo,
            uow=uow
        )
        users = await admin_service.get_all_users()
        ```
    """

    def __init__(
        self,
        db: AsyncSession,
        indexer: ElasticsearchIndexer,
        admin_transaction: AdminTransaction,
    ) -> None:
        """Initialize administrative service with database and dependencies.

        Args:
            db: SQLAlchemy async session for database operations
            indexer: Elasticsearch client for indexing operations
            user_repository: Repository for user database operations
            uow: Unit of work for transaction management
        """
        super().__init__(db)
        self._indexer = Indexer(indexer)
        self._admin_transaction = admin_transaction

    async def get_all_users(
        self,
        search: UserSearch | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[UserRead]:
        """Retrieve all active users with optional filtering and pagination.

        Fetches a list of active users from the database with support for
        filtering by role, username, and email patterns via ilike search.

        Args:
            search: Optional search criteria containing
                role, username, and email filters.
                Defaults to None.
            limit: Maximum number of users to return.
                Defaults to 50.
            offset: Number of users to skip for pagination.
                Defaults to 0.

        Returns:
            list[UserRead]: List of user objects serialized according to UserRead schema

        Raises:
            None

        Example:
            ```python
            users = await service.get_all_users(
                search=UserSearch(role=GlobalUserRole.USER),
                limit=10,
                offset=0
            )
            ```
        """
        users = await self._user_repo.find_many(
            role=search.role if search else None,
            is_active=True,
            ilike=UserIlike(
                username=f"%{search.username if search else None}%",
                email=f"%{search.email if search else None}%",
            ),
            limit=limit,
            offset=offset,
        )
        METRICS.USER_ACTIONS_TOTAL.labels(
            action="admin_list_users", role="admin", status="success"
        ).inc()

        logger.info(
            "Users retrieved: count={count}, limit={limit}, offset={offset}",
            count=len(users),
            limit=limit,
            offset=offset,
        )
        return [UserRead.model_validate(user) for user in users]

    async def delete_user(self, user_id: int, admin_id: int) -> None:
        """Soft-delete a user account with administrative privileges.

        Performs a soft delete by setting is_active=False, ensuring data integrity
        while preventing future authentication. Validates that admin cannot delete
        themselves and prevents deletion of the last remaining admin.

        Args:
            user_id: ID of the user to be deleted.
                Constraints: Must be > 0.
            admin_id: ID of the administrator performing the deletion.
                Constraints: Must be > 0, cannot equal user_id.

        Returns:
            None

        Raises:
            user_exc.UserSelfDeleteError: When admin attempts to delete themselves
            user_exc.UserNotFound: When target user does not exist or is inactive
            user_exc.CannotDeleteLastAdmin: When attempting to delete
                the last admin user

        Example:
            ```python
            await service.delete_user(user_id=5, admin_id=1)
            ```
        """
        if user_id == admin_id:
            logger.warning(
                "Admin {admin_id} attempted to delete themselves",
                admin_id=admin_id,
            )
            raise user_exc.UserSelfDeleteError(message="Cannot delete yourself")

        await self._admin_transaction.delete_user(user_id=user_id, admin_id=admin_id)

        await self._indexer.delete({"type": "user", "id": user_id})

        METRICS.USER_ACTIONS_TOTAL.labels(
            action="admin_delete_user", role="admin", status="success"
        ).inc()
        logger.info(
            "User deleted: user_id={user_id} by admin_id={admin_id}",
            user_id=user_id,
            admin_id=admin_id,
        )

    async def get_stats(self) -> dict[str, Any]:
        """Retrieve system statistics for administrative dashboard.

        Aggregates statistics across all major entities in the system:
        - User statistics: total count, active/inactive breakdown
        - Group statistics: total groups, member counts
        - Task statistics: total tasks, completion rates

        Returns:
            dict[str, Any]: Dictionary containing system statistics by entity type.
                Keys: 'users' (dict), 'groups' (dict), 'tasks' (dict)
                Each value contains entity-specific metrics.

        Raises:
            None

        Example:
            ```python
            stats = await service.get_stats()
            # Returns:
            # {
            #     "users": {"total": 150, "active": 145},
            #     "groups": {"total": 25, "members": 300},
            #     "tasks": {"total": 500, "completed": 350}
            # }
            ```
        """
        METRICS.USER_ACTIONS_TOTAL.labels(
            action="admin_get_stats", role="admin", status="success"
        ).inc()
        stats_users = StatsUsers(self._db)
        stats_groups = StatsGroups(self._db)
        stats_tasks = StatsTasks(self._db)

        result = {
            "users": await stats_users.get_stats(),
            "groups": await stats_groups.get_stats(),
            "tasks": await stats_tasks.get_stats(),
        }

        logger.info(
            "System statistics retrieved: \
                    users={users}, groups={groups}, tasks={tasks}",
            users=result["users"],
            groups=result["groups"],
            tasks=result["tasks"],
        )

        return result


def get_admin_service(
    db: AsyncSession = Depends(db_helper.get_session),
    indexer: ElasticsearchIndexer = Depends(get_es_indexer),
    admin_transaction: AdminTransaction = Depends(get_admin_transaction),
) -> AdminService:
    """Create AdminService instance with dependency injection.

    Factory function for FastAPI dependency injection that creates and configures
    an AdminService instance with all required dependencies.

    Args:
        db: Database session from FastAPI dependency injection.
            Type: AsyncSession.
        indexer: Elasticsearch client from FastAPI dependency injection.
            Type: ElasticsearchIndexer.
        uow: Unit of work from FastAPI dependency injection.
            Type: UnitOfWork.
        user_repository: User repository from FastAPI dependency injection.
            Type: UserRepository.

    Returns:
        AdminService: Configured administrative service instance ready for use

    Example:
        ```python
        @router.get("/admin/users")
        async def get_users(service: AdminService = Depends(get_admin_service)):
            return await service.get_all_users()
        ```
    """
    return AdminService(db=db, indexer=indexer, admin_transaction=admin_transaction)
