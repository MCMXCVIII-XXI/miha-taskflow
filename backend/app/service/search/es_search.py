from typing import Any

from fastapi import Depends

from app.es import ElasticsearchSearch, get_es_search
from app.models import User as UserModel


class ESSearchService:
    def __init__(self, es_search: ElasticsearchSearch):
        self._es_search = es_search

    async def search_tasks(
        self,
        q: str,
        status: str | None,
        priority: str | None,
        group_id: int | None,
        facets: bool,
        limit: int,
        offset: int,
        current_user: UserModel,
    ) -> dict[str, Any]:
        filters: dict[str, Any] = {}
        if status:
            filters["status"] = status
        if priority:
            filters["priority"] = priority
        if group_id:
            filters["group_id"] = group_id

        if facets:
            return await self._es_search.search_tasks_faceted(q, filters, limit, offset)
        else:
            results = await self._es_search.search_tasks(q, filters, limit, offset)
            return {
                "results": results,
                "total": len(results),
                "limit": limit,
                "offset": offset,
            }

    async def search_users(
        self,
        q: str,
        role: str | None,
        is_active: bool | None,
        facets: bool,
        limit: int,
        offset: int,
        current_user: UserModel,
    ) -> dict[str, Any]:
        filters: dict[str, Any] = {}
        if role:
            filters["role"] = role
        if is_active is not None:
            filters["is_active"] = is_active

        if facets:
            return await self._es_search.search_users_faceted(q, filters, limit, offset)
        else:
            results = await self._es_search.search_users(q, filters, limit, offset)
            return {
                "results": results,
                "total": len(results),
                "limit": limit,
                "offset": offset,
            }

    async def search_groups(
        self,
        q: str,
        visibility: str | None,
        join_policy: str | None,
        facets: bool,
        limit: int,
        offset: int,
        current_user: UserModel,
    ) -> dict[str, Any]:
        filters: dict[str, Any] = {}
        if visibility:
            filters["visibility"] = visibility
        if join_policy:
            filters["join_policy"] = join_policy

        if facets:
            return await self._es_search.search_groups_faceted(
                q, filters, limit, offset
            )
        else:
            results = await self._es_search.search_groups(q, filters, limit, offset)
            return {
                "results": results,
                "total": len(results),
                "limit": limit,
                "offset": offset,
            }

    async def search_comments(
        self,
        q: str,
        task_id: int | None,
        user_id: int | None,
        facets: bool,
        limit: int,
        offset: int,
        current_user: UserModel,
    ) -> dict[str, Any]:
        """Search comments with faceted results."""
        filters: dict[str, Any] = {}
        if task_id:
            filters["task_id"] = task_id
        if user_id:
            filters["user_id"] = user_id

        if facets:
            return await self._es_search.search_comments_faceted(
                q, filters, limit, offset
            )
        else:
            results = await self._es_search.search_comments(q, filters, limit, offset)
            return {
                "results": results,
                "total": len(results),
                "limit": limit,
                "offset": offset,
            }

    async def search_notifications(
        self,
        q: str,
        user_id: int | None,
        facets: bool,
        limit: int,
        offset: int,
        current_user: UserModel,
    ) -> dict[str, Any]:
        """Search notifications with faceted results."""
        filters: dict[str, Any] = {}
        if user_id:
            filters["user_id"] = user_id

        if facets:
            return await self._es_search.search_notifications_faceted(
                q, filters, limit, offset
            )
        else:
            results = await self._es_search.search_notifications(
                q, filters, limit, offset
            )
            return {
                "results": results,
                "total": len(results),
                "limit": limit,
                "offset": offset,
            }


def get_es_search_service(
    es: ElasticsearchSearch = Depends(get_es_search),
) -> ESSearchService:
    return ESSearchService(es)
