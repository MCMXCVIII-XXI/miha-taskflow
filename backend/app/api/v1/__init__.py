from fastapi import APIRouter

from .endpoints import auth_router, groups_router, tasks_router, users_router

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(groups_router, prefix="/groups", tags=["groups"])
api_router.include_router(tasks_router, prefix="/tasks", tags=["tasks"])
api_router.include_router(users_router, prefix="/users", tags=["users"])
