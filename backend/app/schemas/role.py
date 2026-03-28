from enum import Enum


class GlobalUserRole(Enum):
    USER = "user"
    ADMIN = "admin"


class SecondaryUserRole(Enum):
    GROUP_ADMIN = "group_admin"
    MEMBER = "member"
    ASSIGNEE = "assignee"
