from .admin import router as admin_router
from .auth import router as auth_router
from .group import router as groups_router
from .task import router as tasks_router
from .user import router as users_router

__all__ = [
    "admin_router",
    "auth_router",
    "groups_router",
    "tasks_router",
    "users_router",
]
