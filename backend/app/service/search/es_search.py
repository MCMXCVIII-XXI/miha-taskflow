from typing import Any

from fastapi import Depends

from app.core.log import logging
from app.core.metrics import METRICS
from app.es import ElasticsearchSearch, get_es_search
from app.models import User as UserModel

logger = logging.get_logger(__name__)


class ESSearchService:
    """
    Service layer for Elasticsearch search functionality.

    Orchestrates search operations for tasks, users, groups, comments,
    and notifications using ElasticsearchSearch. Provides both simple
    search and faceted search with pagination controls.

    Attributes:
        _es_search (ElasticsearchSearch): Low-level Elasticsearch search client
    """

    def __init__(self, es_search: ElasticsearchSearch):
        self._es_search = es_search

    async def _instrumented_search(
        self,
        entity: str,
        search_call: Any,
    ) -> dict[str, Any]:
        """
        Instrumented search wrapper that records metrics and handles exceptions.

        Args:
            entity (str): The entity being searched (e.g., "task", "user", "group")
            search_call (Any): The search function to call

        Returns:
            dict[str, Any]: The search results

        Raises:
            Exception: If the search operation fails
        """
        METRICS.SEARCH_QUERIES_TOTAL.labels(entity=entity, status="success").inc()
        try:
            with METRICS.SEARCH_LATENCY_SECONDS.labels(
                entity=entity, status="success"
            ).time():
                result = await search_call()
            METRICS.SEARCH_QUERIES_TOTAL.labels(entity=entity, status="success").inc()
            logger.info("_instrumented_search success: %s", entity)
            return result
        except Exception:
            logger.error("_instrumented_search failed: %s", entity)
            METRICS.SEARCH_QUERIES_TOTAL.labels(entity=entity, status="error").inc()
            raise

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
        """
        Search tasks with optional filters and faceting.

        Args:
            q (str): Text query for task title/description
            status (str | None): Optional task status filter
            priority (str | None): Optional task priority filter
            group_id (int | None): Optional group ID filter
            facets (bool): Whether to return faceted results
            limit (int): Maximum number of results to return
            offset (int): Number of results to skip for pagination
            current_user (UserModel): Current authenticated user (for logging/context)

        Returns:
            dict[str, Any]: dict with "results", "total", "limit", "offset"
                and "facets" if `facets=True`
        """
        logger.info(
            "search_tasks",
            q=q,
            status=status,
            priority=priority,
            group_id=group_id,
            facets=facets,
            limit=limit,
            offset=offset,
            user_id=current_user.id,
        )

        filters: dict[str, Any] = {}
        if status:
            filters["status"] = status
        if priority:
            filters["priority"] = priority
        if group_id:
            filters["group_id"] = group_id

        if facets:
            result = await self._instrumented_search(
                "task",
                lambda: self._es_search.search_tasks_faceted(q, filters, limit, offset),
            )
            logger.debug(
                "search_tasks_faceted returned", count=len(result.get("results", []))
            )
        else:
            raw = await self._instrumented_search(
                "task", lambda: self._es_search.search_tasks(q, filters, limit, offset)
            )
            result = {
                "results": raw,
                "total": len(raw),
                "limit": limit,
                "offset": offset,
            }
            logger.debug("search_tasks returned", count=len(raw))

        return result

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
        """
        Search users with optional filters and faceting.

        Args:
            q (str): Text query for user attributes
            role (str | None): Optional role filter
            is_active (bool | None): Optional active status filter
            facets (bool): Whether to return faceted results
            limit (int): Maximum number of results to return
            offset (int): Number of results to skip
            current_user (UserModel): Current user (for logging)

        Returns:
            dict[str, Any]: dict with "results", "total", "limit", "offset"
                and "facets" if `facets=True`
        """
        logger.info(
            "search_users",
            q=q,
            role=role,
            is_active=is_active,
            facets=facets,
            limit=limit,
            offset=offset,
            user_id=current_user.id,
        )

        filters: dict[str, Any] = {}
        if role:
            filters["role"] = role
        if is_active is not None:
            filters["is_active"] = is_active

        if facets:
            result = await self._instrumented_search(
                "user",
                lambda: self._es_search.search_users_faceted(q, filters, limit, offset),
            )
            logger.debug(
                "search_users_faceted returned", count=len(result.get("results", []))
            )
        else:
            raw = await self._instrumented_search(
                "user",
                lambda: self._es_search.search_users(q, filters, limit, offset),
            )
            result = {
                "results": raw,
                "total": len(raw),
                "limit": limit,
                "offset": offset,
            }
            logger.debug("search_users returned", count=len(raw))

        return result

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
        """
        Search groups with optional filters and faceting.

        Args:
            q (str): Text query for group name/description
            visibility (str | None): Optional visibility filter
            join_policy (str | None): Optional join policy filter
            facets (bool): Whether to return faceted results
            limit (int): Maximum number of results to return
            offset (int): Number of results to skip
            current_user (UserModel): Current user

        Returns:
            dict[str, Any]: dict with "results", "total", "limit", "offset"
                and "facets" if `facets=True`
        """
        logger.info(
            "search_groups",
            q=q,
            visibility=visibility,
            join_policy=join_policy,
            facets=facets,
            limit=limit,
            offset=offset,
            user_id=current_user.id,
        )

        filters: dict[str, Any] = {}
        if visibility:
            filters["visibility"] = visibility
        if join_policy:
            filters["join_policy"] = join_policy

        if facets:
            result = await self._instrumented_search(
                "group",
                lambda: self._es_search.search_groups_faceted(
                    q, filters, limit, offset
                ),
            )
            logger.debug(
                "search_groups_faceted returned", count=len(result.get("results", []))
            )
        else:
            raw = await self._instrumented_search(
                "group",
                lambda: self._es_search.search_groups(q, filters, limit, offset),
            )
            result = {
                "results": raw,
                "total": len(raw),
                "limit": limit,
                "offset": offset,
            }
            logger.debug("search_groups returned", count=len(raw))

        return result

    async def search_my_groups(
        self,
        current_user: UserModel,
        scope: list[str] | None = None,
        q: str = "",
        visibility: str | None = None,
        join_policy: str | None = None,
        facets: bool = False,
        limit: int = 10,
        offset: int = 0,
    ) -> dict[str, Any]:
        """
        Search "my groups" where current user is admin or member.

        Args:
            current_user (UserModel): Current authenticated user
            scope (list[str] | None): list of scopes:
                "admin", "member" (or both), None = all
            q (str): Optional text query over group name/description/admin_username
            visibility (str | None): Optional visibility filter
            join_policy (str | None): Optional join policy filter
            facets (bool): Whether to return faceted results
            limit (int): Maximum number of results to return
            offset (int): Number of results to skip

        Returns:
            dict[str, Any]: dict with "results", "total", "limit", "offset"
                and "facets" if `facets=True`
        """
        logger.info(
            "search_my_groups",
            user_id=current_user.id,
            scope=scope,
            q=q,
            visibility=visibility,
            join_policy=join_policy,
            facets=facets,
            limit=limit,
            offset=offset,
        )

        filters: dict[str, Any] = {}
        if visibility:
            filters["visibility"] = visibility
        if join_policy:
            filters["join_policy"] = join_policy

        if not facets:
            raw = await self._instrumented_search(
                "my_group",
                lambda: self._es_search.search_my_groups(
                    user_id=current_user.id,
                    scope=scope,
                    query=q,
                    filters=filters,
                    limit=limit,
                    offset=offset,
                ),
            )
            result = {
                "results": raw,
                "total": len(raw),
                "limit": limit,
                "offset": offset,
            }
            logger.debug("search_my_groups returned", count=len(raw))
        else:
            logger.warning(
                "search_my_groups facets not fully implemented yet, \
                    using non-faceted for now"
            )
            raw = await self._instrumented_search(
                "my_group_facets",
                lambda: self._es_search.search_my_groups(
                    user_id=current_user.id,
                    scope=scope,
                    query=q,
                    filters=filters,
                    limit=limit,
                    offset=offset,
                ),
            )
            result = {
                "results": raw,
                "total": len(raw),
                "limit": limit,
                "offset": offset,
                "facets": {},
            }

        return result

    async def search_tasks_by_user(
        self,
        current_user: UserModel,
        scope: list[str] | None = None,
        q: str = "",
        status: str | None = None,
        priority: str | None = None,
        difficulty: str | None = None,
        facets: bool = False,
        limit: int = 10,
        offset: int = 0,
    ) -> dict[str, Any]:
        """
        Search tasks for the current user (assigned, created, etc.).

        Args:
            current_user (UserModel): Current authenticated user
            scope (list[str] | None): list of scopes: \
                "assigned", "created", etc.; None = all tasks
            q (str): Optional text query over title/description/group_name
            status (str | None): Optional task status filter
            priority (str | None): Optional task priority filter
            difficulty (str | None): Optional task difficulty filter
            facets (bool): Whether to return faceted results
            limit (int): Maximum number of results to return
            offset (int): Number of results to skip

        Returns:
            dict[str, Any]: dict with "results", "total", "limit", "offset"
                and "facets" if `facets=True`
        """
        logger.info(
            "search_tasks_by_user",
            user_id=current_user.id,
            scope=scope,
            q=q,
            status=status,
            priority=priority,
            difficulty=difficulty,
            facets=facets,
            limit=limit,
            offset=offset,
        )

        filters: dict[str, Any] = {}
        if status:
            filters["status"] = status
        if priority:
            filters["priority"] = priority
        if difficulty:
            filters["difficulty"] = difficulty

        if not facets:
            raw = await self._instrumented_search(
                "tasks_by_user",
                lambda: self._es_search.search_tasks_by_user(
                    user_id=current_user.id,
                    scope=scope,
                    query=q,
                    filters=filters,
                    limit=limit,
                    offset=offset,
                ),
            )
            result = {
                "results": raw,
                "total": len(raw),
                "limit": limit,
                "offset": offset,
            }
            logger.debug("search_tasks_by_user returned", count=len(raw))
        else:
            logger.warning(
                "search_tasks_by_user facets not fully implemented yet, \
                    using non-faceted for now"
            )
            raw = await self._instrumented_search(
                "tasks_by_user_facets",
                lambda: self._es_search.search_tasks_by_user(
                    user_id=current_user.id,
                    scope=scope,
                    query=q,
                    filters=filters,
                    limit=limit,
                    offset=offset,
                ),
            )
            result = {
                "results": raw,
                "total": len(raw),
                "limit": limit,
                "offset": offset,
                "facets": {},
            }

        return result

    async def search_users_by_group(
        self,
        group_id: int,
        current_user: UserModel,
        q: str = "",
        role: str | None = None,
        is_active: bool | None = None,
        facets: bool = False,
        limit: int = 10,
        offset: int = 0,
    ) -> dict[str, Any]:
        """
        Search users in a specific group (admins + members).

        Args:
            group_id (int): ID of the group
            current_user (UserModel): Current user (for logging/ authorization checks)
            q (str): Optional text query over username/first_name/last_name/email
            role (str | None): Optional role filter
            is_active (bool | None): Optional active status filter
            facets (bool): Whether to return faceted results
            limit (int): Maximum number of results to return
            offset (int): Number of results to skip

        Returns:
            dict[str, Any]: dict with "results", "total", "limit", "offset"
                and "facets" if `facets=True`
        """
        logger.info(
            "search_users_by_group",
            group_id=group_id,
            user_id=current_user.id,
            q=q,
            role=role,
            is_active=is_active,
            facets=facets,
            limit=limit,
            offset=offset,
        )

        filters: dict[str, Any] = {}
        if role:
            filters["role"] = role
        if is_active is not None:
            filters["is_active"] = is_active

        if not facets:
            raw = await self._instrumented_search(
                "users_by_group",
                lambda: self._es_search.search_users_by_group(
                    group_id=group_id,
                    query=q,
                    filters=filters,
                    limit=limit,
                    offset=offset,
                ),
            )
            result = {
                "results": raw,
                "total": len(raw),
                "limit": limit,
                "offset": offset,
            }
            logger.debug("search_users_by_group returned", count=len(raw))
        else:
            logger.warning(
                "search_users_by_group facets not fully implemented yet, \
                    using non-faceted for now"
            )
            raw = await self._instrumented_search(
                "users_by_group_facets",
                lambda: self._es_search.search_users_by_group(
                    group_id=group_id,
                    query=q,
                    filters=filters,
                    limit=limit,
                    offset=offset,
                ),
            )
            result = {
                "results": raw,
                "total": len(raw),
                "limit": limit,
                "offset": offset,
                "facets": {},
            }

        return result

    async def search_tasks_by_group(
        self,
        group_id: int,
        current_user: UserModel,
        q: str = "",
        status: str | None = None,
        priority: str | None = None,
        difficulty: str | None = None,
        spheres: list[str] | None = None,
        assignee_ids: list[int] | None = None,
        facets: bool = False,
        limit: int = 10,
        offset: int = 0,
    ) -> dict[str, Any]:
        """
        Search tasks in a specific group.

        Args:
            group_id (int): ID of the group
            current_user (UserModel): Current user (for logging/auth)
            q (str): Optional text query over title/description/group_name
            status (str | None): Optional task status filter
            priority (str | None): Optional task priority filter
            difficulty (str | None): Optional task difficulty filter
            spheres (list[str] | None): Optional list of spheres filter
            assignee_ids (list[int] | None): Optional list of assignee IDs filter
            facets (bool): Whether to return faceted results
            limit (int): Maximum number of results to return
            offset (int): Number of results to skip

        Returns:
            dict[str, Any]: dict with "results", "total", "limit", "offset"
                and "facets" if `facets=True`
        """
        logger.info(
            "search_tasks_by_group",
            group_id=group_id,
            user_id=current_user.id,
            q=q,
            status=status,
            priority=priority,
            difficulty=difficulty,
            spheres=spheres,
            assignee_ids=assignee_ids,
            facets=facets,
            limit=limit,
            offset=offset,
        )

        filters: dict[str, Any] = {}
        if status:
            filters["status"] = status
        if priority:
            filters["priority"] = priority
        if difficulty:
            filters["difficulty"] = difficulty
        if spheres:
            filters["spheres"] = spheres
        if assignee_ids:
            filters["assignee_ids"] = assignee_ids

        if not facets:
            raw = await self._instrumented_search(
                "tasks_by_group",
                lambda: self._es_search.search_tasks_by_group(
                    group_id=group_id,
                    query=q,
                    filters=filters,
                    limit=limit,
                    offset=offset,
                ),
            )
            result = {
                "results": raw,
                "total": len(raw),
                "limit": limit,
                "offset": offset,
            }
            logger.debug("search_tasks_by_group returned", count=len(raw))
        else:
            logger.warning(
                "search_tasks_by_group facets not fully implemented yet, \
                    using non-faceted for now"
            )
            raw = await self._instrumented_search(
                "tasks_by_group_facets",
                lambda: self._es_search.search_tasks_by_group(
                    group_id=group_id,
                    query=q,
                    filters=filters,
                    limit=limit,
                    offset=offset,
                ),
            )
            result = {
                "results": raw,
                "total": len(raw),
                "limit": limit,
                "offset": offset,
                "facets": {},
            }

        return result

    async def search_my_tasks(
        self,
        current_user: UserModel,
        scope: list[str] | None = None,
        q: str = "",
        status: str | None = None,
        priority: str | None = None,
        difficulty: str | None = None,
        facets: bool = False,
        limit: int = 10,
        offset: int = 0,
    ) -> dict[str, Any]:
        """
        Search tasks for the current user (assigned, created, etc.).

        Args:
            current_user (UserModel): Current authenticated user
            scope (list[str] | None): list of scopes: "assigned", \
                "created", etc.; None = all tasks
            q (str): Optional text query over title/description/group_name
            status (str | None): Optional task status filter
            priority (str | None): Optional task priority filter
            difficulty (str | None): Optional task difficulty filter
            facets (bool): Whether to return faceted results
            limit (int): Maximum number of results to return
            offset (int): Number of results to skip

        Returns:
            dict[str, Any]: dict with "results", "total", "limit", "offset"
                and "facets" if `facets=True`
        """
        logger.info(
            "search_my_tasks",
            user_id=current_user.id,
            scope=scope,
            q=q,
            status=status,
            priority=priority,
            difficulty=difficulty,
            facets=facets,
            limit=limit,
            offset=offset,
        )

        filters: dict[str, Any] = {}
        if status:
            filters["status"] = status
        if priority:
            filters["priority"] = priority
        if difficulty:
            filters["difficulty"] = difficulty

        if not facets:
            raw = await self._instrumented_search(
                "my_tasks",
                lambda: self._es_search.search_tasks_by_user(
                    user_id=current_user.id,
                    scope=scope,
                    query=q,
                    filters=filters,
                    limit=limit,
                    offset=offset,
                ),
            )
            result = {
                "results": raw,
                "total": len(raw),
                "limit": limit,
                "offset": offset,
            }
            logger.debug("search_my_tasks returned", count=len(raw))
        else:
            logger.warning(
                "search_my_tasks facets not fully implemented yet, \
                    using non-faceted for now"
            )
            raw = await self._instrumented_search(
                "my_tasks_facets",
                lambda: self._es_search.search_tasks_by_user(
                    user_id=current_user.id,
                    scope=scope,
                    query=q,
                    filters=filters,
                    limit=limit,
                    offset=offset,
                ),
            )
            result = {
                "results": raw,
                "total": len(raw),
                "limit": limit,
                "offset": offset,
                "facets": {},
            }

        return result

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
        """
        Search comments with optional filters and faceting.

        Args:
            q (str): Text query for comment content/related attributes
            task_id (int | None): Optional task ID filter
            user_id (int | None): Optional user ID filter
            facets (bool): Whether to return faceted results
            limit (int): Maximum number of results to return
            offset (int): Number of results to skip
            current_user (UserModel): Current user

        Returns:
            dict[str, Any]: dict with "results", "total", "limit", "offset"
                and "facets" if `facets=True`
        """
        logger.info(
            "search_comments",
            q=q,
            task_id=task_id,
            user_id=user_id,
            facets=facets,
            limit=limit,
            offset=offset,
        )

        filters: dict[str, Any] = {}
        if task_id:
            filters["task_id"] = task_id
        if user_id:
            filters["user_id"] = user_id

        if facets:
            result = await self._instrumented_search(
                "comments_facets",
                lambda: self._es_search.search_comments_faceted(
                    q, filters, limit, offset
                ),
            )
            logger.debug(
                "search_comments_faceted returned", count=len(result.get("results", []))
            )
        else:
            raw = await self._instrumented_search(
                "comments",
                lambda: self._es_search.search_comments(q, filters, limit, offset),
            )
            result = {
                "results": raw,
                "total": len(raw),
                "limit": limit,
                "offset": offset,
            }
            logger.debug("search_comments returned", count=len(raw))

        return result

    async def search_notifications(
        self,
        q: str,
        user_id: int | None,
        facets: bool,
        limit: int,
        offset: int,
        current_user: UserModel,
    ) -> dict[str, Any]:
        """
        Search notifications with optional filters and faceting.

        Args:
            q (str): Text query for notification attributes
            user_id (int | None): Optional user ID filter (sender/recipient)
            facets (bool): Whether to return faceted results
            limit (int): Maximum number of results to return
            offset (int): Number of results to skip
            current_user (UserModel): Current user

        Returns:
            dict[str, Any]: dict with "results", "total", "limit", "offset"
                and "facets" if `facets=True`
        """
        logger.info(
            "search_notifications",
            q=q,
            user_id=user_id,
            facets=facets,
            limit=limit,
            offset=offset,
        )

        filters: dict[str, Any] = {}
        if user_id:
            filters["user_id"] = user_id

        if facets:
            result = await self._instrumented_search(
                "notifications_facets",
                lambda: self._es_search.search_notifications_faceted(
                    q, filters, limit, offset
                ),
            )
            logger.debug(
                "search_notifications_faceted returned",
                count=len(result.get("results", [])),
            )
        else:
            raw = await self._instrumented_search(
                "notifications",
                lambda: self._es_search.search_notifications(q, filters, limit, offset),
            )
            result = {
                "results": raw,
                "total": len(raw),
                "limit": limit,
                "offset": offset,
            }
            logger.debug("search_notifications returned", count=len(raw))

        return result


def get_es_search_service(
    es: ElasticsearchSearch = Depends(get_es_search),
) -> ESSearchService:
    """
    FastAPI dependency for Elasticsearch search service.

    Args:
        es (ElasticsearchSearch): ElasticsearchSearch instance

    Returns:
        ESSearchService: initialized service
    """
    return ESSearchService(es)
