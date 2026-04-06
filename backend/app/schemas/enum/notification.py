from enum import Enum


class NotificationType(Enum):
    GROUP_INVITE = "group_invite"
    GROUP_JOIN = "group_join"
    TASK_INVITE = "task_invite"
    COMMENT = "comment"
    RATING = "rating"
    FOLLOW = "follow"
    MENTION = "mention"
    LEVEL_UP = "level_up"


class NotificationTargetType(Enum):
    GROUP = "group"
    USER = "user"
    TASK = "task"
    COMMENT = "comment"


class NotificationStatus(Enum):
    READ = "read"
    UNREAD = "unread"
    FAILED = "failed"


class NotificationResponse(Enum):
    ACCEPT = "accept"
    REFUSAL = "refusal"
    WAITING = "waiting"
