from enum import Enum


class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class TaskPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TaskVisibility(Enum):
    PUBLIC = "public"
    PRIVATE = "private"
    GROUP = "group"


class TaskSphere(Enum):
    BACKEND = "backend"
    FRONTEND = "frontend"
    DEVOPS = "devops"
    QA = "qa"
    PRODUCT = "product"


class TaskDifficulty(Enum):
    EASY = 1
    MEDIUM = 3
    HARD = 5

    @property
    def label(self) -> str:
        return self.name.lower()
