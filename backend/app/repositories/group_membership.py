from collections.abc import Sequence

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import UserGroupMembership


class GroupMembershipRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    def _apply_pagination(
        self,
        query: Select[tuple[UserGroupMembership]],
        limit: int | None = None,
        offset: int | None = None,
    ) -> Select[tuple[UserGroupMembership]]:
        if limit is not None:
            query = query.limit(limit)
        if offset is not None:
            query = query.offset(offset)
        return query

    def _build_query(
        self,
        id: int | None = None,
        user_id: int | None = None,
        group_id: int | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> Select[tuple[UserGroupMembership]]:
        query = select(UserGroupMembership)

        if id is not None:
            query = query.where(UserGroupMembership.id == id)
        if user_id is not None:
            query = query.where(UserGroupMembership.user_id == user_id)
        if group_id is not None:
            query = query.where(UserGroupMembership.group_id == group_id)

        return self._apply_pagination(query, limit=limit, offset=offset)

    async def get(
        self,
        id: int | None = None,
        user_id: int | None = None,
        group_id: int | None = None,
    ) -> UserGroupMembership | None:
        query = self._build_query(id=id, user_id=user_id, group_id=group_id)
        return await self._db.scalar(query)

    async def find_many(
        self,
        id: int | None = None,
        user_id: int | None = None,
        group_id: int | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> Sequence[UserGroupMembership]:
        query = self._build_query(
            id=id, user_id=user_id, group_id=group_id, limit=limit, offset=offset
        )

        result = await self._db.scalars(query)
        return result.all()

    async def add(
        self,
        user_id: int,
        group_id: int,
    ) -> UserGroupMembership:
        membership = UserGroupMembership(user_id=user_id, group_id=group_id)
        self._db.add(membership)
        await self._db.flush()
        return membership

    async def get_by_user_and_group(
        self,
        user_id: int,
        group_id: int,
    ) -> UserGroupMembership | None:
        query = (
            select(UserGroupMembership)
            .where(UserGroupMembership.user_id == user_id)
            .where(UserGroupMembership.group_id == group_id)
        )
        return await self._db.scalar(query)

    async def list_by_user(
        self,
        user_id: int,
    ) -> Sequence[UserGroupMembership]:
        query = select(UserGroupMembership).where(
            UserGroupMembership.user_id == user_id
        )
        result = await self._db.scalars(query)
        return result.all()

    async def list_by_group(
        self,
        group_id: int,
    ) -> Sequence[UserGroupMembership]:
        query = select(UserGroupMembership).where(
            UserGroupMembership.group_id == group_id
        )
        result = await self._db.scalars(query)
        return result.all()

    async def delete(
        self,
        membership: UserGroupMembership,
    ) -> None:
        await self._db.delete(membership)
        await self._db.flush()

    async def exists(
        self,
        user_id: int,
        group_id: int,
    ) -> bool:
        query = (
            select(UserGroupMembership)
            .where(UserGroupMembership.user_id == user_id)
            .where(UserGroupMembership.group_id == group_id)
            .limit(1)
        )
        result = await self._db.scalar(query)
        return result is not None
