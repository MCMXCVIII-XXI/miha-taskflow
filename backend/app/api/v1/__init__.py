from fastapi import APIRouter

from .endpoints import tasks, users

api_router = APIRouter()
api_router.include_router(tasks.router, prefix="/api/v1/tasks", tags=["tasks"])
api_router.include_router(users.router, prefix="/api/v1/users", tags=["users"])


__all__ = ["api_router"]
