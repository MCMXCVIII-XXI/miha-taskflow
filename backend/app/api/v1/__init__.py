from fastapi import APIRouter

from .endpoints import (
    admin_router,
    auth_router,
    comment_router,
    groups_router,
    notifications_router,
    tasks_router,
    users_router,
    xp_router,
)

api_router = APIRouter()

api_router.include_router(admin_router, prefix="/admin", tags=["admin"])
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(comment_router, prefix="/tasks", tags=["comments"])
api_router.include_router(groups_router, prefix="/groups", tags=["groups"])
api_router.include_router(
    notifications_router, prefix="/notifications", tags=["notifications"]
)
api_router.include_router(tasks_router, prefix="/tasks", tags=["tasks"])
api_router.include_router(users_router, prefix="/users", tags=["users"])
api_router.include_router(xp_router, prefix="/xp", tags=["xp"])
