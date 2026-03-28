from .auth import router as auth_router
from .group import router as groups_router
from .task import router as tasks_router
from .user import router as users_router

__all__ = ["auth_router", "groups_router", "tasks_router", "users_router"]
