from enum import Enum


class GlobalUserRole(Enum):
    USER = "USER"
    ADMIN = "ADMIN"


class SecondaryUserRole(Enum):
    GROUP_ADMIN = "GROUP_ADMIN"
    MEMBER = "MEMBER"
    ASSIGNEE = "ASSIGNEE"
