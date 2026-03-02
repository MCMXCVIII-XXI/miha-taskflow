import re
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class TaskPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TaskBase(BaseModel):
    """Task API response."""

    id: int = Field(description="Task ID")
    title: str = Field(description="Task title")
    description: str | None = Field(None, description="Task description")
    status: TaskStatus = Field(TaskStatus.PENDING, description="Task status")
    priority: TaskPriority = Field(TaskPriority.MEDIUM, description="Task priority")
    group_id: int | None = Field(None, description="Group ID")
    group_name: str | None = Field(None, description="Group name")
    owner_id: int = Field(description="Task owner ID")
    username: str = Field(description="Task owner username")
    created_at: datetime = Field(description="Task creation date")

    model_config = ConfigDict(from_attributes=True)


class TaskCreate(BaseModel):
    """Task creation."""

    title: str = Field(..., max_length=200, description="Task title")
    description: str | None = Field(
        None, max_length=1000, description="Task description"
    )
    priority: TaskPriority = Field(TaskPriority.MEDIUM, description="Task priority")
    group_id: int | None = Field(None, description="Put task in group")

    @field_validator("title", mode="before")
    @classmethod
    def validate_title(cls, v: str) -> str:
        if len(v) < 3 or len(v) > 200:
            raise ValueError("Title: 3-200 chars")
        if not re.match(r"^[^\s].*[^ ]$", v):
            raise ValueError("Title: no leading/trailing spaces")
        return v.strip()


class TaskUpdate(BaseModel):
    """Task update."""

    title: str | None = Field(None, max_length=200, description="Task title")
    description: str | None = Field(
        None, max_length=1000, description="Task description"
    )
    status: TaskStatus | None = Field(None)
    priority: TaskPriority | None = Field(None)
    is_active: bool | None = Field(None)
