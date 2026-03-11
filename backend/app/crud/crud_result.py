from enum import Enum


class CrudResultTask(Enum):
    NOT_FOUND = "Task not found"
    TITLE_CONFLICT = "Title already exists"


class CrudResultUser(Enum):
    NOT_FOUND = "User not found"
    EMAIL_CONFLICT = "Email already exists"
    USERNAME_CONFLICT = "Username already exists"


class CrudResultGroup(Enum):
    NOT_FOUND = "Group not found"
    NAME_CONFLICT = "Name already exists"


class CrudResultGroupMembership(Enum):
    NOT_FOUND = "Group membership not found"
    MEMBER_CONFLICT = "Member already exists"
