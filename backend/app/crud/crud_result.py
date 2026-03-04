from enum import Enum


class CrudResultTask(Enum):
    NOT_FOUND = "Task not found"
    TITLE_CONFLICT = "Title already exists"


class CrudResultUser(Enum):
    NOT_FOUND = "User not found"
    EMAIL_CONFLICT = "Email already exists"
    USERNAME_CONFLICT = "Username already exists"
