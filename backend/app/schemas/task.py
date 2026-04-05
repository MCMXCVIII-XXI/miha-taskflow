import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .enum import (
    TaskDifficulty,
    TaskPriority,
    TaskSphere,
    TaskStatus,
    TaskVisibility,
)


class TaskSphereWeight(BaseModel):
    """Weight of a task sphere."""

    sphere: TaskSphere = Field(description="Task sphere")
    weight: float = Field(ge=0.1, le=1.0, description="Task sphere weight")

    model_config = ConfigDict(from_attributes=True)


class TaskSpheresInput(BaseModel):
    """Data model for task spheres input."""

    spheres: list[TaskSphereWeight] = Field(
        description="List of task spheres with weights"
    )

    def to_xp_format(self) -> list[dict[str, float | str]]:
        """For XPService.calculate_task_xp()."""
        return [{"sphere": s.sphere.value, "weight": s.weight} for s in self.spheres]


class TaskRead(BaseModel):
    """Task API response."""

    id: int = Field(description="Task ID")
    title: str = Field(description="Task title")
    description: str | None = Field(None, description="Task description")
    status: TaskStatus = Field(TaskStatus.PENDING, description="Task status")
    priority: TaskPriority = Field(TaskPriority.MEDIUM, description="Task priority")
    difficulty: TaskDifficulty | None = Field(None, description="Task difficulty")
    visibility: TaskVisibility = Field(
        TaskVisibility.PRIVATE, description="Task visibility"
    )
    group_id: int | None = Field(None, description="Group ID")
    deadline: datetime | None = Field(None, description="Task deadline")
    created_at: datetime = Field(description="Task creation date")

    model_config = ConfigDict(from_attributes=True)


class TaskCreate(BaseModel):
    """Schema for creating tasks."""

    title: str = Field(..., max_length=200, description="Task title")
    description: str | None = Field(
        None, max_length=1000, description="Task description"
    )
    priority: TaskPriority = Field(TaskPriority.MEDIUM, description="Task priority")
    difficulty: TaskDifficulty | None = Field(
        default=None, description="Task difficulty"
    )
    visibility: TaskVisibility = Field(
        default=TaskVisibility.PRIVATE, description="Task visibility"
    )
    spheres: list[TaskSphereWeight] | None = Field(
        None, description="Task spheres (1-3)"
    )
    group_id: int = Field(description="Put task in group")
    deadline: datetime | None = Field(None, description="Task deadline")

    @field_validator("title", mode="before")
    @classmethod
    def validate_title(cls, v: str) -> str:
        if len(v) < 3 or len(v) > 200:
            raise ValueError("Title: 3-200 chars")
        if not re.match(r"^[^\s].*[^ ]$", v):
            raise ValueError("Title: no leading/trailing spaces")
        return v.strip()


class TaskUpdate(BaseModel):
    """Schema for updating tasks."""

    title: str | None = Field(None, max_length=200, description="Task title")
    description: str | None = Field(
        None, max_length=1000, description="Task description"
    )
    status: TaskStatus | None = Field(None)
    priority: TaskPriority | None = Field(None)
    difficulty: TaskDifficulty | None = Field(None)
    visibility: TaskVisibility | None = Field(None)
    is_active: bool | None = Field(None)
