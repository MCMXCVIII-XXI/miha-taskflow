from enum import Enum


class GroupVisibility(Enum):
    PUBLIC = "public"
    PRIVATE = "private"


class InvitePolicy(Enum):
    ADMIN_ONLY = "admin_only"
    ALL_MEMBERS = "all_members"


class JoinPolicy(Enum):
    OPEN = "open"
    REQUEST = "request"


class JoinRequestStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
