from typing import Any

from fastapi import Depends
from sqlalchemy import Select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.log import get_logger
from app.db import db_helper

# MODELS
from app.models import User as UserModel
from app.models import UserGroup as UserGroupModel

# SCHEMAS
from app.schemas import UserRead, UserSearch, UserUpdate

from .base import BaseService
from .exceptions import group_exc, user_exc
from .query_db import GroupQueries, UserQueries
from .search import user_search

logger = get_logger("service.user")


class UserService(BaseService):
    """
    User lifecycle management service with advanced search and profile operations.

    Details:
        Complete user CRUD with FastAPI DI, zero-DB profile
            retrieval via JWT dependency,
        advanced search with @user_search Redis caching,
            conflict-checked partial updates,
        soft-delete pattern (is_active=False), group admin access validation.

    Attributes:
        _db (AsyncSession): SQLAlchemy async database session
        _user_queries (UserQueries): User-specific optimized query builders
        _group_queries (GroupQueries): Group membership query helpers

    Methods:
        _get_my_group(group_id, user_id) → UserGroupModel
        _assert_active_current_user(current_user) → UserModel
        get_my_profile(current_user) → UserRead
        search_users() → Select[tuple[UserModel]]
        search_users_in_group(group_id) → Select[tuple[UserModel]]
        search_users_in_tasks(task_id) → Select[tuple[UserModel]]
        update_my_profile(current_user, user_in) → UserRead
        delete_my_profile(current_user) → None
        get_group_admin(group_id) → UserRead
        get_owner_task(task_id) → UserRead

    Returns:
        UserRead, Select[tuple[UserModel]], UserGroupModel, None

    Raises:
        user_exc.UserNotFound
        user_exc.UserEmailConflict
        user_exc.UserUsernameConflict
        group_exc.ForbiddenGroupAccess

    Example Usage:
        user_svc = UserService(db)
        profile = await user_svc.get_my_profile(current_user)
        users = await user_svc.search_users()
        await user_svc.update_my_profile(current_user, user_update)
    """

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db)
        self._user_queries = UserQueries
        self._group_queries = GroupQueries

    async def _get_my_group(self, group_id: int, user_id: int) -> UserGroupModel:
        """
        Retrieve group where user is administrator/owner with authorization check.

        Details:
            Internal helper for admin-only group operations.
            Single scalar query via GroupQueries.by_admin_group.
            Only active groups (is_active=True).
            Fast ownership validation before group mutations.

        Arguments:
            group_id (int): Target group ID
            user_id (int): User ID to verify as admin

        Returns:
            UserGroupModel: Active group where user is admin

        Raises:
            group_exc.ForbiddenGroupAccess: User not admin or group inactive

        Example Usage:
            group = await self._get_my_group(group_id, current_user.id)
            group.name = "New Name"
        """
        group = await self._db.scalar(
            self._group_queries.by_admin_group(user_id, group_id, is_active=True)
        )

        if not group:
            raise group_exc.ForbiddenGroupAccess(
                message="You are not the owner of the group"
            )

        return group

    async def _assert_active_current_user(self, current_user: UserModel) -> UserModel:
        """
        Validate that provided user is active and return it.

        Details:
            Fast validation helper for current_user dependency.
            Raises UserNotFound if user.is_active == False.

        Arguments:
            current_user (UserModel): User from JWT dependency.

        Returns:
            UserModel: Active user instance.

        Raises:
            user_exc.UserNotFound: If user is inactive.

        Example Usage:
            user = await self._assert_active_current_user(current_user)
            return UserRead.model_validate(user)
        """
        if not current_user.is_active:
            raise user_exc.UserNotFound(message="User not found")
        return current_user

    async def get_my_profile(self, current_user: UserModel) -> UserRead:
        """
        Get current authenticated user's profile without extra DB lookup.

        Details:
            Zero database calls optimization using JWT current_user dependency.
            Validates user activity via _assert_active_current_user helper.

        Arguments:
            current_user (UserModel): Authenticated user model from dependency.

        Returns:
            UserRead: Current user's profile.

        Raises:
            user_exc.UserNotFound: If current user is inactive.

        Example Usage:
            return await user_svc.get_my_profile(current_user)
        """
        user = await self._assert_active_current_user(current_user)
        return UserRead.model_validate(user)

    @user_search
    async def search_users(
        self,
        search: UserSearch,
        sort: UserSearch,
        limit: int,
        offset: int,
        **kwargs: Any,
    ) -> Select[tuple[UserModel]]:
        """
        Search all active users query builder.

        Details:
            Returns SQLAlchemy Select query for active users (is_active=True).
            @user_search decorator prepares for search/filter execution.
            Used for user autocomplete and lists.

        Returns:
            Select[tuple[UserModel]]: SQLAlchemy query for active users.

        Example Usage:
            users = await user_svc.search_users()
            results = await user_svc._db.execute(users)
        """
        return self._user_queries.all(is_active=True)

    @user_search
    async def search_users_in_group(
        self,
        group_id: int,
        search: UserSearch,
        sort: UserSearch,
        limit: int,
        offset: int,
    ) -> Select[tuple[UserModel]]:
        """
        Search active users in specific group query.

        Details:
            Returns SQLAlchemy Select for group members (is_active=True).
            @user_search decorator prepares filtering.

        Arguments:
            group_id (int): Target group ID.

        Returns:
            Select[tuple[UserModel]]: Group member query.

        Example Usage:
            group_users = await user_svc.search_users_in_group(group_id=123)
        """
        return self._user_queries.by_group_membership(group_id, is_active=True)

    @user_search
    async def search_users_in_tasks(
        self,
        task_id: int,
        search: UserSearch,
        sort: UserSearch,
        limit: int,
        offset: int,
    ) -> Select[tuple[UserModel]]:
        """
        Search active task assignees query.

        Details:
            Returns SQLAlchemy Select for task assignees (is_active=True).
            @user_search decorator prepares filtering.

        Arguments:
            task_id (int): Target task ID.

        Returns:
            Select[tuple[UserModel]]: Task assignee query.

        Example Usage:
            task_users = await user_svc.search_users_in_tasks(task_id=456)
        """
        return self._user_queries.by_task_assignee(task_id, is_active=True)

    async def update_my_profile(
        self, current_user: UserModel, user_in: UserUpdate
    ) -> UserRead:
        """
        Update current authenticated user's profile.

        Details:
            Updates only changed fields via model_dump(exclude_unset=True).
            Separate conflict checks for email/username with dedicated exceptions.
            Automatic cache invalidation for "users" namespace.

        Arguments:
            current_user (UserModel): Authenticated user model from dependency.
            user_in (UserUpdate): Update payload.

        Returns:
            UserSchema: Updated profile.

        Raises:
            user_exc.UserNotFound: If user is inactive.
            user_exc.UserEmailConflict: If email is already used.
            user_exc.UserUsernameConflict: If username is already used.
        Example Usage:
            user_update = UserUpdate(email="new@example.com")
            updated = await user_svc.update_my_profile(current_user, user_update)
        """
        user = await self._assert_active_current_user(current_user)
        update_data = user_in.model_dump(exclude_unset=True)

        email = update_data.get("email")
        username = update_data.get("username")

        if email:
            email_conflict = await self._db.scalar(
                self._user_queries.by_email(email, is_active=True).where(
                    UserModel.id != user.id
                )
            )
            if email_conflict:
                logger.warning(
                    "Profile update failed: duplicate email {email} for user {user_id}",
                    email=email,
                    user_id=user.id,
                )
                raise user_exc.UserEmailConflict(
                    message="User with this email already exists"
                )

        if username:
            username_conflict = await self._db.scalar(
                self._user_queries.by_username(username, is_active=True).where(
                    UserModel.id != user.id,
                )
            )
            if username_conflict:
                logger.warning(
                    "Profile update failed: duplicate username {username} \
                        for user {user_id}",
                    username=username,
                    user_id=user.id,
                )
                raise user_exc.UserUsernameConflict(
                    message="User with this username already exists"
                )

        for field, value in update_data.items():
            setattr(user, field, value)

        await self._db.commit()
        await self._db.refresh(user)
        await self._invalidate("auth")

        logger.info(
            "Profile updated: user_id={user_id}, fields={fields}",
            user_id=user.id,
            fields=list(update_data.keys()),
        )

        return UserRead.model_validate(user)

    async def delete_my_profile(self, current_user: UserModel) -> None:
        """
        Soft-delete current authenticated user.

        Details:
            Sets user.is_active = False (soft delete pattern).
            Automatic cache invalidation for "auth" namespace.

        Arguments:
            current_user (UserModel): Authenticated user model from dependency.

        Raises:
            user_exc.UserNotFound: If user is inactive.

        Example Usage:
            ```python
            await user_svc.delete_my_profile(current_user)
        ```
        """
        user = await self._assert_active_current_user(current_user)
        user.is_active = False
        await self._db.commit()
        await self._invalidate("users")
        await self._invalidate("auth")

        logger.info(
            "Profile deleted (soft delete): user_id={user_id}",
            user_id=user.id,
        )

    async def get_group_admin(self, group_id: int) -> UserRead:
        """
        Retrieve group administrator profile.

        Details:
            Only group members can access admin profile.
            Uses direct admin_id from UserGroup model.
            Returns active admin only.

        Arguments:
            group_id (int): Target group ID
            current_user (UserModel): Authenticated user (must be group member)

        Returns:
            UserRead: Group admin profile

        Raises:
            user_exc.UserNotFound: Admin not found or inactive.

        Example Usage:
            admin = await user_svc.get_group_admin(group_id=123, current_user)
        """
        admin = await self._db.scalar(
            self._user_queries.get_admin_group(group_id, is_active=True)
        )
        if not admin:
            raise user_exc.UserNotFound(message="Not found admin")
        return UserRead.model_validate(admin)

    async def get_owner_task(
        self,
        task_id: int,
    ) -> UserRead:
        """
        Get task owner (group admin) profile.

        Details:
            Retrieves task → group → owner chain.
            Returns active owner only.

        Arguments:
            task_id (int): Task ID
            current_user (UserModel): Authenticated user

        Returns:
            UserRead: Task owner profile

        Example Usage:
            owner = await user_svc.get_owner_task(task_id=456, current_user)
        """

        owner = await self._db.scalar(
            self._user_queries.by_owner_task(task_id, is_active=True)
        )
        if not owner:
            raise user_exc.UserNotFound(message="Task owner not found")
        return UserRead.model_validate(owner)


def get_user_service(db: AsyncSession = Depends(db_helper.get_session)) -> UserService:
    """
    FastAPI dependency factory for UserService injection.

    Details:
        Dependency injection helper for FastAPI routes.
        Automatically creates UserService instance with database session.
        Follows FastAPI dependency pattern for service layer isolation.

        Usage in routers:
            @router.get("/profile")
            async def get_profile(
                user_service: UserService = Depends(get_user_service),
                current_user: UserModel = Depends(get_current_user)
            ):
                return await user_service.get_my_profile(current_user)

    Arguments:
        db (AsyncSession): Database session from db_helper.get_session

    Returns:
        UserService: Fresh UserService instance with injected DB session

    Example Usage:
        @app.get("/users/search")
        async def search_users(
            user_service: UserService = Depends(get_user_service)
        ):
    """
    return UserService(db)
