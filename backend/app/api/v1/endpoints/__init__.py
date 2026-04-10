from .admin import router as admin_router
from .auth import router as auth_router
from .comment import router as comment_router
from .group import router as groups_router
from .notification import router as notifications_router
from .rating import router as rating_router
from .search import router as search_router
from .task import router as tasks_router
from .user import router as users_router
from .xp import router as xp_router

__all__ = [
    "admin_router",
    "auth_router",
    "comment_router",
    "groups_router",
    "notifications_router",
    "rating_router",
    "search_router",
    "tasks_router",
    "users_router",
    "xp_router",
]
