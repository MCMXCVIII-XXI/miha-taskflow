from fastapi import APIRouter

from .endpoints import groups, login, tasks, users

api_router = APIRouter()
api_router.include_router(tasks.router, prefix="/api/v1/tasks", tags=["tasks"])
api_router.include_router(users.router, prefix="/api/v1/users", tags=["users"])
api_router.include_router(groups.router, prefix="/api/v1/groups", tags=["groups"])
api_router.include_router(login.router, prefix="/api/v1/login", tags=["login"])


__all__ = ["api_router"]
