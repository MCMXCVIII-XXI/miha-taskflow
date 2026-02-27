from datetime import datetime
from enum import Enum

from sqlmodel import Field, SQLModel


class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class TaskPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TaskBase(SQLModel):
    title: str = Field(max_length=200)
    description: str | None = Field(max_length=1000, default=None)
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM


class TaskCreate(TaskBase):
    pass


class TaskUpdate(SQLModel):
    title: str | None = None
    status: TaskStatus | None = None


class Task(TaskBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
