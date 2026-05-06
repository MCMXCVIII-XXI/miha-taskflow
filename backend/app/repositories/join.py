from collections.abc import Sequence

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import JoinRequest
from app.schemas.enum import JoinRequestStatus


class JoinRequestRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    def _apply_pagination(
        self,
        query: Select[tuple[JoinRequest]],
        limit: int | None = None,
        offset: int | None = None,
    ) -> Select[tuple[JoinRequest]]:
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
        task_id: int | None = None,
        status: JoinRequestStatus | None = None,
    ) -> Select[tuple[JoinRequest]]:
        query = select(JoinRequest)

        if id is not None:
            query = query.where(JoinRequest.id == id)
        if user_id is not None:
            query = query.where(JoinRequest.user_id == user_id)
        if group_id is not None:
            query = query.where(JoinRequest.group_id == group_id)
        if task_id is not None:
            query = query.where(JoinRequest.task_id == task_id)
        if status is not None:
            query = query.where(JoinRequest.status == status)

        return query

    async def get(
        self,
        id: int | None = None,
        user_id: int | None = None,
        group_id: int | None = None,
        task_id: int | None = None,
        status: JoinRequestStatus | None = None,
    ) -> JoinRequest | None:
        query = self._build_query(
            id=id,
            user_id=user_id,
            group_id=group_id,
            task_id=task_id,
            status=status,
        )
        return await self._db.scalar(query)

    async def find_many(
        self,
        id: int | None = None,
        user_id: int | None = None,
        group_id: int | None = None,
        task_id: int | None = None,
        status: JoinRequestStatus | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> Sequence[JoinRequest]:
        query = self._build_query(
            id=id,
            user_id=user_id,
            group_id=group_id,
            task_id=task_id,
            status=status,
        )
        query = self._apply_pagination(query, limit=limit, offset=offset)

        result = await self._db.scalars(query)
        return result.all()

    async def add(
        self,
        user_id: int,
        group_id: int | None = None,
        task_id: int | None = None,
        status: JoinRequestStatus = JoinRequestStatus.PENDING,
    ) -> JoinRequest:
        join_request = JoinRequest(
            user_id=user_id,
            group_id=group_id,
            task_id=task_id,
            status=status,
        )
        self._db.add(join_request)
        await self._db.flush()
        return join_request

    async def update(
        self,
        join_request: JoinRequest,
        status: JoinRequestStatus | None = None,
    ) -> JoinRequest:
        if status is not None:
            join_request.status = status
        await self._db.flush()
        return join_request
