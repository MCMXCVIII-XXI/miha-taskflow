from fastapi import APIRouter

from .endpoints import tasks

api_router = APIRouter()
api_router.include_router(tasks.router, prefix="/api/v1/tasks", tags=["tasks"])
