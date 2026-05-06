from collections.abc import Sequence
from typing import Any, Literal

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models import Task, UserGroup, UserGroupMembership, UserRole
from app.schemas.enum import GroupVisibility, InvitePolicy, JoinPolicy


class GroupRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    def _apply_pagination(
        self,
        query: Select[tuple[UserGroup]],
        limit: int | None = None,
        offset: int | None = None,
    ) -> Select[tuple[UserGroup]]:
        if limit is not None:
            query = query.limit(limit)
        if offset is not None:
            query = query.offset(offset)
        return query

    def _check_active_group(
        self,
        query: Select[tuple[UserGroup]],
        is_active: Literal[True, False, None],
    ) -> Select[tuple[UserGroup]]:
        if is_active is None:
            return query
        return query.where(UserGroup.is_active == is_active)

    def _check_active_count(
        self,
        query: Select[tuple[int]],
        is_active: Literal[True, False, None],
    ) -> Select[tuple[int]]:
        if is_active is None:
            return query
        return query.where(UserGroup.is_active == is_active)

    def _build_query(
        self,
        id: int | None = None,
        name: str | None = None,
        visibility: GroupVisibility | None = None,
        join_policy: JoinPolicy | None = None,
        level: int | None = None,
        invite_policy: InvitePolicy | None = None,
        admin_id: int | None = None,
        is_active: bool | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> Select[tuple[UserGroup]]:
        query = select(UserGroup)

        if id is not None:
            query = query.where(UserGroup.id == id)
        if name is not None:
            query = query.where(UserGroup.name == name)
        if visibility is not None:
            query = query.where(UserGroup.visibility == visibility)
        if join_policy is not None:
            query = query.where(UserGroup.join_policy == join_policy)
        if level is not None:
            query = query.where(UserGroup.level == level)
        if invite_policy is not None:
            query = query.where(UserGroup.invite_policy == invite_policy)
        if admin_id is not None:
            query = query.where(UserGroup.admin_id == admin_id)
        query = self._apply_pagination(query, limit=limit, offset=offset)
        return self._check_active_group(query, is_active)

    async def get(
        self,
        id: int | None = None,
        name: str | None = None,
        visibility: GroupVisibility | None = None,
        join_policy: JoinPolicy | None = None,
        level: int | None = None,
        invite_policy: InvitePolicy | None = None,
        admin_id: int | None = None,
        is_active: bool | None = None,
    ) -> UserGroup | None:
        query = self._build_query(
            id=id,
            name=name,
            visibility=visibility,
            join_policy=join_policy,
            level=level,
            invite_policy=invite_policy,
            admin_id=admin_id,
            is_active=is_active,
        )
        return await self._db.scalar(query)

    async def find_many(
        self,
        id: int | None = None,
        name: str | None = None,
        visibility: GroupVisibility | None = None,
        join_policy: JoinPolicy | None = None,
        level: int | None = None,
        invite_policy: InvitePolicy | None = None,
        admin_id: int | None = None,
        is_active: bool | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> Sequence[UserGroup]:
        query = self._build_query(
            id=id,
            name=name,
            visibility=visibility,
            join_policy=join_policy,
            level=level,
            invite_policy=invite_policy,
            admin_id=admin_id,
            is_active=is_active,
            limit=limit,
            offset=offset,
        )

        result = await self._db.scalars(query)
        return result.all()

    async def add(
        self,
        name: str,
        admin_id: int,
        visibility: GroupVisibility,
        level: int,
        join_policy: JoinPolicy,
        invite_policy: InvitePolicy,
        parent_group_id: int | None = None,
        description: str | None = None,
    ) -> UserGroup:
        group = UserGroup(
            name=name,
            description=description,
            admin_id=admin_id,
            visibility=visibility,
            parent_group_id=parent_group_id,
            level=level,
            join_policy=join_policy,
            invite_policy=invite_policy,
        )
        self._db.add(group)
        await self._db.flush()
        return group

    async def update(
        self,
        group: UserGroup,
        group_update: dict[str, Any] | None = None,
    ) -> UserGroup:
        if not group_update:
            return group

        for key, value in group_update.items():
            setattr(group, key, value)
        await self._db.flush()
        return group

    async def get_groups_by_member(
        self,
        user_id: int,
        is_active: bool | None = None,
    ) -> Sequence[UserGroup]:
        query = (
            select(UserGroup)
            .join(UserGroupMembership, UserGroupMembership.group_id == UserGroup.id)
            .where(UserGroupMembership.user_id == user_id)
        )

        result = await self._db.scalars(self._check_active_group(query, is_active))
        return result.all()

    async def get_admin_group_ids(
        self,
        user_id: int,
        is_active: bool | None = None,
    ) -> Sequence[int]:
        query = (
            select(UserGroup.id)
            .join(UserRole, UserRole.group_id == UserGroup.id)
            .where(UserRole.user_id == user_id)
        )

        result = await self._db.scalars(self._check_active_count(query, is_active))
        return result.all()

    async def get_group_by_task(
        self,
        task_id: int,
        is_active: bool | None = None,
    ) -> UserGroup | None:
        query = (
            select(UserGroup)
            .join(Task, Task.group_id == UserGroup.id)
            .where(Task.id == task_id)
        )
        return await self._db.scalar(self._check_active_group(query, is_active))

    async def delete(
        self,
        group: UserGroup,
    ) -> None:
        await self._db.delete(group)
        await self._db.flush()

    def get_group_select(
        self,
        id: int | None = None,
        name: str | None = None,
        visibility: GroupVisibility | None = None,
        join_policy: JoinPolicy | None = None,
        level: int | None = None,
        invite_policy: InvitePolicy | None = None,
        admin_id: int | None = None,
        is_active: bool | None = None,
    ) -> Select[tuple[UserGroup]]:
        return self._build_query(
            id=id,
            name=name,
            visibility=visibility,
            join_policy=join_policy,
            level=level,
            invite_policy=invite_policy,
            admin_id=admin_id,
            is_active=is_active,
        )

    def by_my_member_select(
        self,
        user_id: int,
        is_active: bool | None = None,
    ) -> Select[tuple[UserGroup]]:
        query = (
            select(UserGroup)
            .join(UserGroupMembership, UserGroupMembership.group_id == UserGroup.id)
            .where(UserGroupMembership.user_id == user_id)
        )
        return self._check_active_group(query, is_active)

    async def get_with_admin(
        self, group_id: int, is_active: bool = True
    ) -> UserGroup | None:
        stmt = (
            select(UserGroup)
            .where(UserGroup.id == group_id)
            .where(UserGroup.is_active == is_active)
            .options(joinedload(UserGroup.admin))
        )
        return await self._db.scalar(stmt)
