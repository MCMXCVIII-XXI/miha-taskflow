"""Examples for Swagger documentation."""

from .admin_examples import AdminExamples
from .auth_examples import AuthExamples
from .comment_examples import CommentExamples
from .group_examples import (
    GroupExamples,
    GroupMemberExamples,
    GroupRequestExamples,
    GroupSearchExamples,
    GroupTaskExamples,
)
from .notification_examples import NotificationExamples, SSEExamples
from .search_examples import SearchExamples
from .task_examples import TaskAssignExamples, TaskExamples, TaskSearchExamples
from .user_examples import UserExamples, UserGroupExamples, UserSearchExamples
from .xp_rating_examples import RatingExamples, XPExamples

__all__ = [
    "AdminExamples",
    "AuthExamples",
    "CommentExamples",
    "GroupExamples",
    "GroupMemberExamples",
    "GroupRequestExamples",
    "GroupSearchExamples",
    "GroupTaskExamples",
    "NotificationExamples",
    "RatingExamples",
    "SSEExamples",
    "SearchExamples",
    "TaskAssignExamples",
    "TaskExamples",
    "TaskSearchExamples",
    "UserExamples",
    "UserGroupExamples",
    "UserSearchExamples",
    "XPExamples",
]
