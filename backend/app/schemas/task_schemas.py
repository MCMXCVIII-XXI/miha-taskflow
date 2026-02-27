from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class TaskPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TaskCreate(BaseModel):
    """
    Task create schema.
    """

    title: str = Field(max_length=200, description="Task title")
    description: str | None = Field(max_length=1000, default=None, description="Task description")
    status: TaskStatus = Field(TaskStatus.PENDING, description="Task status")
    priority: TaskPriority = Field(TaskPriority.MEDIUM, description="Task priority")


class TaskBase(BaseModel):
    """
    Base class for task schemas.
    """

    id: int = Field(description="Task ID")
    title: str = Field(max_length=200, description="Task title")
    description: str | None = Field(max_length=1000, default=None, description="Task description")
    status: TaskStatus = Field(description="Task status")
    priority: TaskPriority = Field(description="Task priority")
    created_at: datetime = Field(default_factory=datetime.now, description="Task creation date")
    is_active: bool = Field(default=True, description="Task is active")

    model_config = ConfigDict(from_attributes=True)


class TaskUpdate(BaseModel):
    """
    Task update schema.
    """

    title: str | None = Field(max_length=200, description="Task title")
    description: str | None = Field(max_length=1000, description="Task description")
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    is_active: bool | None = None

    model_config = ConfigDict(from_attributes=True)
