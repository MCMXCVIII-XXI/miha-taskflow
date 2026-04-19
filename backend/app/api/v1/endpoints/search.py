from typing import Any

from fastapi import APIRouter, Depends, Query
from fastapi_cache.decorator import cache

from app.cache import search_key
from app.core.permission import require_permissions_db
from app.models import User as UserModel
from app.service.search import ESSearchService, get_es_search_service

router = APIRouter()


@router.get("/tasks/search")
@cache(expire=300, key_builder=search_key)
async def search_tasks(
    q: str = Query(default=""),
    status: str | None = Query(default=None),
    priority: str | None = Query(default=None),
    group_id: int | None = Query(default=None),
    facets: bool = Query(default=True),
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
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


@router.get("/users/search")
@cache(expire=300, key_builder=search_key)
async def search_users(
    q: str = Query(default=""),
    role: str | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    facets: bool = Query(default=True),
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
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


@router.get("/groups/search")
@cache(expire=300, key_builder=search_key)
async def search_groups(
    q: str = Query(default=""),
    visibility: str | None = Query(default=None),
    join_policy: str | None = Query(default=None),
    facets: bool = Query(default=True),
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
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


@router.get("/comments/search")
@cache(expire=300, key_builder=search_key)
async def search_comments(
    q: str = Query(default=""),
    task_id: int | None = Query(default=None),
    user_id: int | None = Query(default=None),
    facets: bool = Query(default=True),
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
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


@router.get("/notifications/search")
@cache(expire=300, key_builder=search_key)
async def search_notifications(
    q: str = Query(default=""),
    user_id: int | None = Query(default=None),
    facets: bool = Query(default=True),
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
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


@router.get("/groups/my")
@cache(expire=300, key_builder=search_key)
async def search_my_groups(
    scope: list[str] | None = Query(default=None),
    q: str = Query(default=""),
    visibility: str | None = Query(default=None),
    join_policy: str | None = Query(default=None),
    facets: bool = Query(default=True),
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
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


@router.get("/tasks/my")
@cache(expire=300, key_builder=search_key)
async def search_my_tasks(
    scope: list[str] | None = Query(default=None),
    q: str = Query(default=""),
    status: str | None = Query(default=None),
    priority: str | None = Query(default=None),
    difficulty: str | None = Query(default=None),
    facets: bool = Query(default=True),
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
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


@router.get("/users/by-group")
@cache(expire=300, key_builder=search_key)
async def search_users_by_group(
    group_id: int = Query(),
    q: str = Query(default=""),
    role: str | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    facets: bool = Query(default=True),
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
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


@router.get("/tasks/by-group")
@cache(expire=300, key_builder=search_key)
async def search_tasks_by_group(
    group_id: int = Query(),
    q: str = Query(default=""),
    status: str | None = Query(default=None),
    priority: str | None = Query(default=None),
    difficulty: str | None = Query(default=None),
    spheres: list[str] | None = Query(
        default=None,
    ),
    assignee_ids: list[int] | None = Query(
        default=None,
    ),
    facets: bool = Query(default=True),
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
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
