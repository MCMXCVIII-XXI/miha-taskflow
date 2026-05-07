from typing import Any

from fastapi import APIRouter, Depends, Query
from fastapi_cache.decorator import cache

from app.cache import search_key
from app.core.permission import require_permissions_db
from app.examples.search_examples import SearchExamples
from app.models import User as UserModel
from app.service.search import ESSearchService, get_es_search_service

router = APIRouter(tags=["search"])


@router.get(
    "/tasks/search",
    summary="Search tasks",
    response_model=dict[str, Any],
    description="""
    Full-text search tasks via Elasticsearch.

    **Permissions required:** GROUP_MEMBER or higher

    **Query parameters:**
    - `q` (optional): Search query string
    - `status` (optional): Filter by status (PENDING, IN_PROGRESS, DONE, CANCELLED)
    - `priority` (optional): Filter by priority (HIGH, MEDIUM, LOW)
    - `group_id` (optional): Filter by group ID
    - `facets` (default: true): Include facetaggregations
    - `limit` (default: 10, max: 100)
    - `offset` (default: 0)

    **Caching:** Results cached for 5 minutes (Redis).
    """,
    responses={
        200: {
            "description": "Search results",
            "content": {"application/json": {"example": SearchExamples.SEARCH_TASKS}},
        },
    },
)
@cache(expire=300, key_builder=search_key)
async def search_tasks(
    q: str = Query("", description="Search query"),
    status: str | None = Query(None, description="Filter by status"),
    priority: str | None = Query(None, description="Filter by priority"),
    group_id: int | None = Query(None, description="Filter by group"),
    facets: bool = Query(True, description="Include facets"),
    limit: int = Query(10, ge=1, le=100, description="Max results"),
    offset: int = Query(0, ge=0, description="Result offset"),
    current_user: UserModel = Depends(require_permissions_db("task:view:any")),
    svc: ESSearchService = Depends(get_es_search_service),
) -> dict[str, Any]:
    """Search tasks with faceted results."""
    return await svc.search_tasks(
        q=q,
        status=status,
        priority=priority,
        group_id=group_id,
        facets=facets,
        limit=limit,
        offset=offset,
        current_user=current_user,
    )


@router.get(
    "/users/search",
    summary="Search users",
    response_model=dict[str, Any],
    description="""
    Full-text search users via Elasticsearch.

    **Permissions required:** AUTHENTICATED_USER

    **Query parameters:**
    - `q` (optional): Search query string
    - `role` (optional): Filter by role
    - `is_active` (optional): Filter by active status
    - `facets` (default: true): Include facet aggregations
    - `limit` (default: 10, max: 100)
    - `offset` (default: 0)

    **Caching:** Results cached for 5 minutes (Redis).
    """,
    responses={
        200: {
            "description": "Search results",
            "content": {"application/json": {"example": SearchExamples.SEARCH_USERS}},
        },
    },
)
@cache(expire=300, key_builder=search_key)
async def search_users(
    q: str = Query("", description="Search query"),
    role: str | None = Query(None, description="Filter by role"),
    is_active: bool | None = Query(None, description="Filter by active status"),
    facets: bool = Query(True, description="Include facets"),
    limit: int = Query(10, ge=1, le=100, description="Max results"),
    offset: int = Query(0, ge=0, description="Result offset"),
    current_user: UserModel = Depends(require_permissions_db("user:view:any")),
    svc: ESSearchService = Depends(get_es_search_service),
) -> dict[str, Any]:
    """Search users with faceted results."""
    return await svc.search_users(
        q=q,
        role=role,
        is_active=is_active,
        facets=facets,
        limit=limit,
        offset=offset,
        current_user=current_user,
    )


@router.get(
    "/groups/search",
    summary="Search groups",
    response_model=dict[str, Any],
    description="""
    Full-text search groups via Elasticsearch.

    **Permissions required:** AUTHENTICATED_USER

    **Query parameters:**
    - `q` (optional): Search query string
    - `visibility` (optional): Filter by visibility (PUBLIC, INTERNAL, PRIVATE)
    - `join_policy` (optional): Filter by join policy (OPEN, REQUEST, INVITE)
    - `facets` (default: true): Include facet aggregations
    - `limit` (default: 10, max: 100)
    - `offset` (default: 0)

    **Caching:** Results cached for 5 minutes (Redis).
    """,
    responses={
        200: {
            "description": "Search results",
            "content": {"application/json": {"example": SearchExamples.SEARCH_GROUPS}},
        },
    },
)
@cache(expire=300, key_builder=search_key)
async def search_groups(
    q: str = Query("", description="Search query"),
    visibility: str | None = Query(None, description="Filter by visibility"),
    join_policy: str | None = Query(None, description="Filter by join policy"),
    facets: bool = Query(True, description="Include facets"),
    limit: int = Query(10, ge=1, le=100, description="Max results"),
    offset: int = Query(0, ge=0, description="Result offset"),
    current_user: UserModel = Depends(require_permissions_db("group:view:any")),
    svc: ESSearchService = Depends(get_es_search_service),
) -> dict[str, Any]:
    """Search groups with faceted results."""
    return await svc.search_groups(
        q=q,
        visibility=visibility,
        join_policy=join_policy,
        facets=facets,
        limit=limit,
        offset=offset,
        current_user=current_user,
    )


@router.get(
    "/comments/search",
    summary="Search comments",
    response_model=dict[str, Any],
    description="""
    Full-text search comments via Elasticsearch.

    **Permissions required:** GROUP_MEMBER

    **Query parameters:**
    - `q` (optional): Search query string
    - `task_id` (optional): Filter by task ID
    - `user_id` (optional): Filter by user ID
    - `facets` (default: true): Include facet aggregations
    - `limit` (default: 10, max: 100)
    - `offset` (default: 0)

    **Caching:** Results cached for 5 minutes (Redis).
    """,
    responses={
        200: {
            "description": "Search results",
        },
    },
)
@cache(expire=300, key_builder=search_key)
async def search_comments(
    q: str = Query("", description="Search query"),
    task_id: int | None = Query(None, description="Filter by task"),
    user_id: int | None = Query(None, description="Filter by user"),
    facets: bool = Query(True, description="Include facets"),
    limit: int = Query(10, ge=1, le=100, description="Max results"),
    offset: int = Query(0, ge=0, description="Result offset"),
    current_user: UserModel = Depends(require_permissions_db("comment:view:any")),
    svc: ESSearchService = Depends(get_es_search_service),
) -> dict[str, Any]:
    """Search comments with faceted results."""
    return await svc.search_comments(
        q=q,
        task_id=task_id,
        user_id=user_id,
        facets=facets,
        limit=limit,
        offset=offset,
        current_user=current_user,
    )


@router.get(
    "/notifications/search",
    summary="Search notifications",
    response_model=dict[str, Any],
    description="""
    Full-text search notifications via Elasticsearch.

    **Permissions required:** AUTHENTICATED_USER

    **Query parameters:**
    - `q` (optional): Search query string
    - `user_id` (optional): Filter by user ID
    - `facets` (default: true): Include facet aggregations
    - `limit` (default: 10, max: 100)
    - `offset` (default: 0)

    **Caching:** Results cached for 5 minutes (Redis).
    """,
    responses={
        200: {
            "description": "Search results",
        },
    },
)
@cache(expire=300, key_builder=search_key)
async def search_notifications(
    q: str = Query("", description="Search query"),
    user_id: int | None = Query(None, description="Filter by user"),
    facets: bool = Query(True, description="Include facets"),
    limit: int = Query(10, ge=1, le=100, description="Max results"),
    offset: int = Query(0, ge=0, description="Result offset"),
    current_user: UserModel = Depends(require_permissions_db("notification:view:own")),
    svc: ESSearchService = Depends(get_es_search_service),
) -> dict[str, Any]:
    """Search notifications with faceted results."""
    return await svc.search_notifications(
        q=q,
        user_id=user_id,
        facets=facets,
        limit=limit,
        offset=offset,
        current_user=current_user,
    )


@router.get(
    "/groups/my",
    summary="Search my groups",
    response_model=dict[str, Any],
    description="""
    Search groups the current user is a member of.

    **Permissions required:** GROUP_MEMBER

    **Query parameters:**
    - `scope` (optional): Filter by membership scope (OWNER, ADMIN, MEMBER)
    - `q` (optional): Search query string
    - `visibility` (optional): Filter by visibility
    - `join_policy` (optional): Filter by join policy
    - `facets` (default: true): Include facet aggregations
    - `limit` (default: 10, max: 100)
    - `offset` (default: 0)

    **Caching:** Results cached for 5 minutes (Redis).
    """,
    responses={
        200: {
            "description": "Search results",
        },
    },
)
@cache(expire=300, key_builder=search_key)
async def search_my_groups(
    scope: list[str] | None = Query(None, description="Filter by scope"),
    q: str = Query("", description="Search query"),
    visibility: str | None = Query(None, description="Filter by visibility"),
    join_policy: str | None = Query(None, description="Filter by join policy"),
    facets: bool = Query(True, description="Include facets"),
    limit: int = Query(10, ge=1, le=100, description="Max results"),
    offset: int = Query(0, ge=0, description="Result offset"),
    current_user: UserModel = Depends(require_permissions_db("group:view:own")),
    svc: ESSearchService = Depends(get_es_search_service),
) -> dict[str, Any]:
    """Search my groups."""
    return await svc.search_my_groups(
        current_user=current_user,
        scope=scope,
        q=q,
        visibility=visibility,
        join_policy=join_policy,
        facets=facets,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/tasks/my",
    summary="Search my tasks",
    response_model=dict[str, Any],
    description="""
    Search tasks the current user is involved in.

    **Permissions required:** GROUP_MEMBER

    **Query parameters:**
    - `scope` (optional): Filter by involvement (CREATOR, LEADER, ASSIGNEE)
    - `q` (optional): Search query string
    - `status` (optional): Filter by status
    - `priority` (optional): Filter by priority
    - `difficulty` (optional): Filter by difficulty
    - `facets` (default: true): Include facet aggregations
    - `limit` (default: 10, max: 100)
    - `offset` (default: 0)

    **Caching:** Results cached for 5 minutes (Redis).
    """,
    responses={
        200: {
            "description": "Search results",
        },
    },
)
@cache(expire=300, key_builder=search_key)
async def search_my_tasks(
    scope: list[str] | None = Query(None, description="Filter by scope"),
    q: str = Query("", description="Search query"),
    status: str | None = Query(None, description="Filter by status"),
    priority: str | None = Query(None, description="Filter by priority"),
    difficulty: str | None = Query(None, description="Filter by difficulty"),
    facets: bool = Query(True, description="Include facets"),
    limit: int = Query(10, ge=1, le=100, description="Max results"),
    offset: int = Query(0, ge=0, description="Result offset"),
    current_user: UserModel = Depends(require_permissions_db("task:view:own")),
    svc: ESSearchService = Depends(get_es_search_service),
) -> dict[str, Any]:
    """Search my tasks."""
    return await svc.search_my_tasks(
        current_user=current_user,
        scope=scope,
        q=q,
        status=status,
        priority=priority,
        difficulty=difficulty,
        facets=facets,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/users/by-group",
    summary="Search users in group",
    response_model=dict[str, Any],
    description="""
    Search users within a specific group.

    **Permissions required:** GROUP_MEMBER

    **Query parameters:**
    - `group_id` (required): Group ID to search within
    - `q` (optional): Search query string
    - `role` (optional): Filter by role (OWNER, ADMIN, MEMBER)
    - `is_active` (optional): Filter by active status
    - `facets` (default: true): Include facet aggregations
    - `limit` (default: 10, max: 100)
    - `offset` (default: 0)

    **Caching:** Results cached for 5 minutes (Redis).
    """,
    responses={
        200: {
            "description": "Search results",
        },
    },
)
@cache(expire=300, key_builder=search_key)
async def search_users_by_group(
    group_id: int = Query(..., description="Group ID"),
    q: str = Query("", description="Search query"),
    role: str | None = Query(None, description="Filter by role"),
    is_active: bool | None = Query(None, description="Filter by active status"),
    facets: bool = Query(True, description="Include facets"),
    limit: int = Query(10, ge=1, le=100, description="Max results"),
    offset: int = Query(0, ge=0, description="Result offset"),
    current_user: UserModel = Depends(require_permissions_db("user:view:any")),
    svc: ESSearchService = Depends(get_es_search_service),
) -> dict[str, Any]:
    """Search users in a specific group (admins + members)."""
    return await svc.search_users_by_group(
        group_id=group_id,
        current_user=current_user,
        q=q,
        role=role,
        is_active=is_active,
        facets=facets,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/tasks/by-group",
    summary="Search tasks by group",
    response_model=dict[str, Any],
    description="""
    Search tasks within a specific group.

    **Permissions required:** GROUP_MEMBER

    **Query parameters:**
    - `group_id` (required): Group ID to search within
    - `q` (optional): Search query string
    - `status` (optional): Filter by status
    - `priority` (optional): Filter by priority
    - `difficulty` (optional): Filter by difficulty
    - `spheres` (optional): Filter by spheres
    - `assignee_ids` (optional): Filter by assignee IDs
    - `facets` (default: true): Include facet aggregations
    - `limit` (default: 10, max: 100)
    - `offset` (default: 0)

    **Caching:** Results cached for 5 minutes (Redis).
    """,
    responses={
        200: {
            "description": "Search results",
        },
    },
)
@cache(expire=300, key_builder=search_key)
async def search_tasks_by_group(
    group_id: int = Query(..., description="Group ID"),
    q: str = Query("", description="Search query"),
    status: str | None = Query(None, description="Filter by status"),
    priority: str | None = Query(None, description="Filter by priority"),
    difficulty: str | None = Query(None, description="Filter by difficulty"),
    spheres: list[str] | None = Query(None, description="Filter by spheres"),
    assignee_ids: list[int] | None = Query(None, description="Filter by assignees"),
    facets: bool = Query(True, description="Include facets"),
    limit: int = Query(10, ge=1, le=100, description="Max results"),
    offset: int = Query(0, ge=0, description="Result offset"),
    current_user: UserModel = Depends(require_permissions_db("task:view:any")),
    svc: ESSearchService = Depends(get_es_search_service),
) -> dict[str, Any]:
    """Search tasks by group."""
    return await svc.search_tasks_by_group(
        group_id=group_id,
        current_user=current_user,
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
