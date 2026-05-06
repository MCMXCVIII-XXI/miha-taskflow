from collections.abc import Sequence
from typing import Any, Literal

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Task,
    TaskAssignee,
    User,
    UserGroup,
    UserGroupMembership,
)
from app.schemas.enum import GlobalUserRole

from .dict import UserIlike


class UserRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    def _apply_pagination(
        self,
        query: Select[tuple[User]],
        limit: int | None = None,
        offset: int | None = None,
    ) -> Select[tuple[User]]:
        if limit is not None:
            query = query.limit(limit)
        if offset is not None:
            query = query.offset(offset)
        return query

    def _check_active_user(
        self,
        query: Select[tuple[User]],
        is_active: Literal[True, False, None],
    ) -> Select[tuple[User]]:
        if is_active is None:
            return query
        return query.where(User.is_active == is_active)

    def _check_active_count(
        self,
        query: Select[tuple[int]],
        is_active: Literal[True, False, None],
    ) -> Select[tuple[int]]:
        if is_active is None:
            return query
        return query.where(User.is_active == is_active)

    def _apply_ilike(
        self,
        query: Select[tuple[User]],
        ilike: UserIlike | None,
    ) -> Select[tuple[User]]:
        """Apply ilike filters from UserIlikeDict to query."""
        if ilike is None:
            return query
        if "username" in ilike:
            query = query.where(User.username.ilike(ilike["username"]))
        if "email" in ilike:
            query = query.where(User.email.ilike(ilike["email"]))
        if "first_name" in ilike:
            query = query.where(User.first_name.ilike(ilike["first_name"]))
        if "last_name" in ilike:
            query = query.where(User.last_name.ilike(ilike["last_name"]))
        if "patronymic" in ilike:
            query = query.where(User.patronymic.ilike(ilike["patronymic"]))
        return query

    def _build_query(
        self,
        id: int | None = None,
        id_in: list[int] | None = None,
        username: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        patronymic: str | None = None,
        email: str | None = None,
        role: GlobalUserRole | None = None,
        is_active: Literal[True, False, None] = None,
        ilike: UserIlike | None = None,
    ) -> Select[tuple[User]]:
        query = select(User)

        if id is not None:
            query = query.where(User.id == id)
        if id_in is not None:
            query = query.where(User.id.in_(id_in))
        if username is not None:
            query = query.where(User.username == username)
        if first_name is not None:
            query = query.where(User.first_name == first_name)
        if last_name is not None:
            query = query.where(User.last_name == last_name)
        if patronymic is not None:
            query = query.where(User.patronymic == patronymic)
        if email is not None:
            query = query.where(User.email == email)
        if role is not None:
            query = query.where(User.role == role)

        query = self._apply_ilike(query, ilike)
        return self._check_active_user(query, is_active)

    def _exlcude_user_id(
        self, query: Select[tuple[User]], user_id: int
    ) -> Select[tuple[User]]:
        if user_id:
            query = query.where(User.id != user_id)
        return query

    def _exclude_user_id_count(
        self, query: Select[tuple[int]], user_id: int
    ) -> Select[tuple[int]]:
        if user_id:
            query = query.where(User.id != user_id)
        return query

    def _build_count_query(
        self,
        id: int | None = None,
        username: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        patronymic: str | None = None,
        email: str | None = None,
        role: GlobalUserRole | None = None,
        is_active: Literal[True, False, None] = None,
        exclude_user_id: int | None = None,
    ) -> Select[tuple[int]]:
        query = select(func.count(User.id)).select_from(User)
        query = self._build_count_query(
            id=id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            patronymic=patronymic,
            email=email,
            role=role,
            is_active=is_active,
        )
        query = (
            self._exclude_user_id_count(query=query, user_id=exclude_user_id)
            if exclude_user_id
            else query
        )
        return query

    async def get(
        self,
        id: int | None = None,
        id_in: list[int] | None = None,
        username: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        patronymic: str | None = None,
        email: str | None = None,
        role: GlobalUserRole | None = None,
        is_active: Literal[True, False, None] = None,
        ilike: UserIlike | None = None,
        exclude_user_id: int | None = None,
    ) -> User | None:
        query = self._build_query(
            id=id,
            id_in=id_in,
            username=username,
            first_name=first_name,
            last_name=last_name,
            patronymic=patronymic,
            email=email,
            role=role,
            is_active=is_active,
            ilike=ilike,
        )
        return await self._db.scalar(query)

    async def find_many(
        self,
        id: int | None = None,
        id_in: list[int] | None = None,
        username: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        patronymic: str | None = None,
        email: str | None = None,
        role: GlobalUserRole | None = None,
        is_active: Literal[True, False, None] = None,
        ilike: UserIlike | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> Sequence[User]:
        query = self._build_query(
            id=id,
            id_in=id_in,
            username=username,
            first_name=first_name,
            last_name=last_name,
            patronymic=patronymic,
            email=email,
            role=role,
            is_active=is_active,
            ilike=ilike,
        )
        query = self._apply_pagination(query, limit=limit, offset=offset)

        result = await self._db.scalars(query)
        return result.all()

    async def count(
        self,
        id: int | None = None,
        username: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        patronymic: str | None = None,
        email: str | None = None,
        role: GlobalUserRole | None = None,
        is_active: Literal[True, False, None] = None,
    ) -> int:
        query = self._build_count_query(
            id=id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            patronymic=patronymic,
            email=email,
            role=role,
            is_active=is_active,
        )
        return await self._db.scalar(query) or 0

    async def get_by_email_or_username(
        self,
        email: str,
        username: str,
        is_active: Literal[True, False, None] = None,
    ) -> User | None:
        query = select(User).where((User.email == email) | (User.username == username))
        return await self._db.scalar(self._check_active_user(query, is_active))

    async def by_group_membership(
        self,
        group_id: int,
        is_active: Literal[True, False, None] = None,
    ) -> Sequence[User]:
        query = (
            select(User)
            .join(UserGroupMembership, UserGroupMembership.user_id == User.id)
            .where(UserGroupMembership.group_id == group_id)
        )

        result = await self._db.scalars(self._check_active_user(query, is_active))
        return result.all()

    async def get_admin_group(
        self,
        group_id: int,
        is_active: Literal[True, False, None] = None,
    ) -> User | None:
        query = (
            select(User)
            .join(UserGroup, UserGroup.admin_id == User.id)
            .where(UserGroup.id == group_id)
        )
        return await self._db.scalar(self._check_active_user(query, is_active))

    async def by_task_assignee(
        self,
        task_id: int,
        is_active: Literal[True, False, None] = None,
    ) -> Sequence[User]:
        query = (
            select(User)
            .join(TaskAssignee, TaskAssignee.user_id == User.id)
            .where(TaskAssignee.task_id == task_id)
        )

        result = await self._db.scalars(self._check_active_user(query, is_active))
        return result.all()

    async def by_task(
        self,
        task_id: int,
        is_active: Literal[True, False, None] = None,
    ) -> Sequence[User]:
        query = (
            select(User)
            .join(UserGroup, UserGroup.admin_id == User.id)
            .join(Task, Task.group_id == UserGroup.id)
            .where(Task.id == task_id)
        )

        result = await self._db.scalars(self._check_active_user(query, is_active))
        return result.all()

    async def update(
        self, user: User, user_update: dict[str, Any] | None = None
    ) -> User:
        if not user_update:
            return user
        for field, value in user_update.items():
            setattr(user, field, value)
        await self._db.flush()
        return user

    async def delete(
        self,
        id: int,
        is_active: bool | None = None,
    ) -> User | None:
        user = await self.get(id=id, is_active=is_active)
        if user is None:
            return None
        if is_active is not None:
            user.is_active = is_active
        await self._db.flush()
        return user

    async def add(
        self,
        username: str,
        email: str,
        first_name: str,
        last_name: str,
        patronymic: str | None,
        hashed_password: str,
    ) -> User:
        """Create new user. Used in RegistrationService via UnitOfWork."""
        user = User(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            patronymic=patronymic,
            hashed_password=hashed_password,
        )
        self._db.add(user)
        await self._db.flush()
        return user

    async def get_user(
        self,
        id: int | None = None,
        id_in: list[int] | None = None,
        username: str | None = None,
        email: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        exclude_user_id: int | None = None,
        is_active: Literal[True, False, None] = None,
    ) -> Sequence[User]:
        query = self._build_query(
            id=id,
            id_in=id_in,
            username=username,
            email=email,
            is_active=is_active,
        )
        query = self._apply_pagination(query, limit=limit, offset=offset)
        if exclude_user_id is not None:
            query = query.where(User.id != exclude_user_id)
        result = await self._db.scalars(query)
        return result.all()

    async def by_group_membership_select(
        self,
        group_id: int,
        limit: int | None = None,
        offset: int | None = None,
        is_active: Literal[True, False, None] = None,
    ) -> Sequence[User]:
        query = (
            select(User)
            .join(UserGroupMembership, UserGroupMembership.user_id == User.id)
            .where(UserGroupMembership.group_id == group_id)
        )
        query = self._check_active_user(query, is_active)
        query = self._apply_pagination(query, limit=limit, offset=offset)
        result = await self._db.scalars(query)
        return result.all()

    async def by_owner_task(
        self,
        task_id: int,
        is_active: Literal[True, False, None] = None,
    ) -> User | None:
        query = (
            select(User)
            .join(UserGroup, UserGroup.admin_id == User.id)
            .join(Task, Task.group_id == UserGroup.id)
            .where(Task.id == task_id)
        )
        query = self._check_active_user(query, is_active)
        return await self._db.scalar(query)
