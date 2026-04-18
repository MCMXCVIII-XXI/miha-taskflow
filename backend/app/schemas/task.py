import re
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .enum import (
    TaskDifficulty,
    TaskPriority,
    TaskSphere,
    TaskStatus,
    TaskVisibility,
)


class TaskSphereWeight(BaseModel):
    """Task sphere weight configuration for XP distribution."""

    sphere: TaskSphere = Field(description="Target skill sphere for XP distribution")
    weight: float = Field(
        ge=0.1, le=1.0, description="Weight for XP distribution (0.1-1.0)"
    )

    model_config = ConfigDict(from_attributes=True)


class TaskSpheresInput(BaseModel):
    """Input schema for task spheres configuration."""

    spheres: list[TaskSphereWeight] = Field(
        description="List of task spheres with weights for XP distribution"
    )

    def to_xp_format(self) -> list[dict[str, float | str]]:
        """Convert to format expected by XPService.calculate_task_xp()."""
        return [{"sphere": s.sphere.value, "weight": s.weight} for s in self.spheres]


class TaskRead(BaseModel):
    """Task response schema for API endpoints."""

    id: int = Field(description="Unique task identifier")
    title: str = Field(description="Task title (summary)")
    description: str | None = Field(None, description="Detailed task description")
    status: TaskStatus = Field(TaskStatus.PENDING, description="Current task status")
    priority: TaskPriority = Field(
        TaskPriority.MEDIUM, description="Task priority level"
    )
    difficulty: TaskDifficulty | None = Field(
        None, description="Task difficulty rating"
    )
    visibility: TaskVisibility = Field(
        TaskVisibility.PRIVATE, description="Task visibility scope"
    )
    group_id: int | None = Field(
        None, description="ID of the group this task belongs to"
    )
    spheres: list[dict[str, Any]] | None = Field(
        None, description="Task spheres configuration"
    )
    deadline: datetime | None = Field(None, description="Task deadline date and time")
    created_at: datetime = Field(description="Task creation timestamp")
    updated_at: datetime | None = Field(None, description="Last task update timestamp")

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
    group_id: int | None = Field(None, description="Put task in group")
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
    status: TaskStatus | None = Field(default=None, description="Task status")
    priority: TaskPriority | None = Field(default=None, description="Task priority")
    difficulty: TaskDifficulty | None = Field(
        default=None, description="Task difficulty"
    )
    visibility: TaskVisibility | None = Field(
        default=None, description="Task visibility"
    )
    is_active: bool | None = Field(default=None, description="Task active status")
    deadline: datetime | None = Field(default=None, description="Task deadline")
