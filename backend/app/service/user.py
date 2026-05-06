"""User service for user profile and account management.

This module provides the UserService class for managing user profiles,
including retrieval, updates, and search operations.

**Key Components:**
* `UserService`: Main service class for user operations;
* `get_user_service`: FastAPI dependency injection factory.

**Dependencies:**
* `UserRepository`: User data access layer;
* `UnitOfWork`: Transaction management;
* `ElasticsearchIndexer`: Search index management;
* `XPService`: XP and skills lookup service.

**Usage Example:**
    ```python
    from app.service.user import get_user_service

    @router.get("/users/me")
    async def get_my_profile(
        user_svc: UserService = Depends(get_user_service),
        current_user: User = Depends(get_current_user)
    ):
        return await user_svc.get_my_profile(current_user)
    ```

**Notes:**
- Read operations use injected db session directly;
- Write operations use UnitOfWork for atomic transactions;
- Profiles are indexed in Elasticsearch for search functionality;
- Soft delete is used (is_active=False) rather than hard deletion.
"""

from typing import Any

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.log import logging
from app.core.metrics import (
    METRICS,
)
from app.db import db_helper
from app.es import ElasticsearchIndexer, get_es_indexer
from app.models import User as UserModel
from app.schemas import UserRead, UserUpdate

from .base import BaseService
from .exceptions import user_exc
from .transactions.user import UserTransaction, get_user_transaction
from .utils import Indexer
from .xp import XPService, get_xp_service

logger = logging.get_logger(__name__)


class UserService(BaseService):
    """Service for user profile and account management operations.

    Handles user profile retrieval, updates, search, and account deletion.
    Provides clear separation between read and write operations with
    UnitOfWork for transactional integrity.

    Attributes:
        _db (AsyncSession): SQLAlchemy async session for database operations
        _user_repo (UserRepository): Repository for user data operations
        _xp_service (XPService): Service for XP and skills lookups
        _indexer (Indexer): Elasticsearch indexer wrapper for search operations
        _uow (UnitOfWork): Unit of work for transaction management

    Example:
        ```python
        user_service = UserService(
            db=session,
            indexer=indexer,
            xp_service=xp_svc,
            uow=uow
        )
        profile = await user_service.get_my_profile(current_user)
        ```
    """

    def __init__(
        self,
        db: AsyncSession,
        indexer: ElasticsearchIndexer,
        xp_service: XPService,
        user_transaction: UserTransaction,
    ) -> None:
        """Initialize UserService with dependencies.

        Args:
            db: SQLAlchemy async session for database operations
            indexer: Elasticsearch client for indexing operations
            xp_service: Service for XP and skills lookups
            uow: Unit of work for transactional operations
        """
        super().__init__(db)
        self._xp_service = xp_service
        self._indexer = Indexer(indexer)
        self._user_transaction = user_transaction

    async def _assert_active_current_user(self, current_user: UserModel) -> UserModel:
        """Ensure the current user is active and log access.

        Validates that the current user account is active before allowing
        profile access or modifications. This is a security checkpoint
        that prevents inactive users from performing operations.

        Args:
            current_user: The authenticated user to validate
                Type: UserModel

        Returns:
            UserModel: The validated active user

        Raises:
            user_exc.UserNotFound: When user account is inactive

        Example:
            ```python
            user = await self._assert_active_current_user(current_user)
            # Proceed with operations on validated user
            ```
        """
        if not current_user.is_active:
            logger.warning(
                "User access denied: user {user_id} is inactive",
                user_id=current_user.id,
            )
            raise user_exc.UserNotFound(message="User not found")

        logger.info("User accessed: user_id={user_id}", user_id=current_user.id)
        return current_user

    async def get_my_profile(self, current_user: UserModel) -> UserRead:
        """Return the current authenticated user's profile.

        Retrieves and validates the current user's profile. Uses the injected
        db session for read-only access.

        Args:
            current_user: The authenticated user requesting their profile
                Type: UserModel

        Returns:
            UserRead: User profile serialized according to UserRead schema

        Raises:
            user_exc.UserNotFound: When user account is inactive

        Example:
            ```python
            profile = await user_svc.get_my_profile(current_user)
            ```
        """
        user = await self._assert_active_current_user(current_user)
        METRICS.USER_ACTIONS_TOTAL.labels(
            action="get_profile", role="user", status="success"
        ).inc()
        return UserRead.model_validate(user)

    async def get_user(self, user_id: int) -> dict[str, Any]:
        """Return a public user profile together with top skills.

        Retrieves a user's public profile along with their top skills
        for display in user directories or profiles.

        Args:
            user_id: ID of the user to retrieve
                Type: int
                Constraints: Must be > 0

        Returns:
            dict[str, Any]: Dictionary containing UserRead data plus top_skills list

        Raises:
            user_exc.UserNotFound: When user not found or inactive

        Example:
            ```python
            profile = await user_svc.get_user(user_id=123)
            # Returns: {"id": 123, "username": "john", "top_skills": [...], ...}
            ```
        """
        user = await self._user_repo.get(id=user_id, is_active=True)
        if user is None:
            raise user_exc.UserNotFound(message=f"User with id {user_id} not found")

        top_skills = await self._xp_service.get_top_skills(user_id, 3) or []
        METRICS.USER_ACTIONS_TOTAL.labels(
            action="get_user", role="user", status="success"
        ).inc()

        logger.info(
            "User profile retrieved: user_id={user_id}, top_skills_count={count}",
            user_id=user_id,
            count=len(top_skills),
        )

        return {
            **UserRead.model_validate(user).model_dump(),
            "top_skills": top_skills,
        }

    async def update_my_profile(
        self,
        current_user: UserModel,
        user_in: UserUpdate,
    ) -> UserRead:
        """Update the current user's profile inside a unit of work.

        Uses the UnitOfWork context to ensure all changes to the user
        and related entities are applied atomically. Validates email
        and username uniqueness before applying updates.

        Args:
            current_user: The authenticated user updating their profile
                Type: UserModel
            user_in: Updated profile data
                Type: UserUpdate

        Returns:
            UserRead: Updated user profile serialized according to UserRead schema

        Raises:
            user_exc.UserNotFound: When user not found
            user_exc.UserEmailConflict: When email already in use
            user_exc.UserUsernameConflict: When username already in use

        Example:
            ```python
            updated = await user_svc.update_my_profile(
                current_user,
                UserUpdate(email="new@example.com")
            )
            ```
        """
        user = await self._assert_active_current_user(current_user)
        user_update = user_in.model_dump(exclude_unset=True)
        db_user = await self._user_transaction.update_my_profile(user, user_update)

        METRICS.USER_ACTIONS_TOTAL.labels(
            action="update_profile", role="user", status="success"
        ).inc()
        await self._indexer.index(user)
        await self._invalidate("auth")

        logger.info(
            "Profile updated: user_id={user_id}, fields={fields}",
            user_id=db_user.id,
            fields=list(user_update.keys()),
        )
        return UserRead.model_validate(db_user)

    async def delete_my_profile(self, current_user: UserModel) -> None:
        """Soft-delete the current authenticated user inside a unit of work.

        Performs a soft delete by setting is_active=False, preserving
        user data while preventing future authentication. Uses UnitOfWork
        for transactional integrity.

        Args:
            current_user: The authenticated user deleting their profile
                Type: UserModel

        Returns:
            None

        Raises:
            user_exc.UserNotFound: When user not found

        Example:
            ```python
            await user_svc.delete_my_profile(current_user)
            ```
        """
        user = await self._assert_active_current_user(current_user)
        await self._user_transaction.delete_my_profile(user)

        METRICS.USER_ACTIONS_TOTAL.labels(
            action="delete_profile", role="user", status="success"
        ).inc()

        await self._indexer.delete({"type": "user", "id": current_user.id})
        await self._invalidate("users")
        await self._invalidate("auth")

        logger.info(
            "Profile deleted (soft delete): user_id={user_id}",
            user_id=user.id,
        )

    async def get_group_admin(self, group_id: int) -> UserRead:
        """Return the active administrator of a group.

        Retrieves the user who is the admin (owner) of a specific group.

        Args:
            group_id: ID of the group
                Type: int
                Constraints: Must be > 0

        Returns:
            UserRead: Admin user profile serialized according to UserRead schema

        Raises:
            user_exc.UserNotFound: When admin not found

        Example:
            ```python
            admin = await user_svc.get_group_admin(group_id=123)
            ```
        """
        admin = await self._user_repo.get_admin_group(group_id=group_id, is_active=True)

        METRICS.USER_ACTIONS_TOTAL.labels(
            action="get_group_admin", role="admin", status="success"
        ).inc()
        if not admin:
            raise user_exc.UserNotFound(message="Not found admin")

        logger.info(
            "Group admin retrieved: group_id={group_id}, admin_id={user_id}",
            group_id=group_id,
            user_id=admin.id,
        )

        return UserRead.model_validate(admin)

    async def get_owner_task(self, task_id: int) -> UserRead:
        """Return the active owner of a task.

        Retrieves the group admin who owns the group that contains
        the specified task.

        Args:
            task_id: ID of the task
                Type: int
                Constraints: Must be > 0

        Returns:
            UserRead: Owner user profile serialized according to UserRead schema

        Raises:
            user_exc.UserNotFound: When owner not found

        Example:
            ```python
            owner = await user_svc.get_owner_task(task_id=123)
            ```
        """
        owner = await self._user_repo.by_owner_task(task_id=task_id, is_active=True)
        METRICS.USER_ACTIONS_TOTAL.labels(
            action="get_owner_task", role="owner", status="success"
        ).inc()
        if not owner:
            raise user_exc.UserNotFound(message="Task owner not found")

        logger.info(
            "Task owner retrieved: task_id={task_id}, owner_id={user_id}",
            task_id=task_id,
            user_id=owner.id,
        )

        return UserRead.model_validate(owner)


def get_user_service(
    db: AsyncSession = Depends(db_helper.get_session),
    indexer: ElasticsearchIndexer = Depends(get_es_indexer),
    xp_service: XPService = Depends(get_xp_service),
    user_transaction: UserTransaction = Depends(get_user_transaction),
) -> UserService:
    """Create UserService instance with dependency injection.

    Factory function for FastAPI dependency injection that creates and configures
    a UserService instance with all required dependencies.

    Args:
        db: Database session from FastAPI dependency injection.
            Type: AsyncSession.
        indexer: Elasticsearch client from FastAPI dependency injection.
            Type: ElasticsearchIndexer.
        xp_service: XP service from FastAPI dependency injection.
            Type: XPService.
        uow: Unit of work from FastAPI dependency injection.
            Type: UnitOfWork.

    Returns:
        UserService: Configured user service instance

    Example:
        ```python
        @router.get("/users/me")
        async def get_my_profile(
            user_svc: UserService = Depends(get_user_service),
            current_user: User = Depends(get_current_user)
        ):
            return await user_svc.get_my_profile(current_user)
        ```
    """
    return UserService(
        db=db,
        indexer=indexer,
        xp_service=xp_service,
        user_transaction=user_transaction,
    )
