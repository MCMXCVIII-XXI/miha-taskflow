from datetime import datetime
from typing import Any, ClassVar

from elasticsearch.dsl import (
    AsyncDocument,
    Boolean,
    Date,
    Integer,
    Keyword,
    M,
    Text,
    mapped_field,
)

from app.models import Task
from app.schemas import TaskRead

from .utils import RUSSIAN_ANALYZER_SETTINGS, get_index_name


class TaskDoc(AsyncDocument):
    """Elasticsearch document structure for task full-text search."""

    id: M[int] = mapped_field(Integer())
    title: M[str] = mapped_field(Text(analyzer="task_analyzer"))
    description: M[str] = mapped_field(Text(analyzer="task_analyzer"))
    status: M[str] = mapped_field(Keyword())
    priority: M[str] = mapped_field(Keyword())
    difficulty: M[str | None] = mapped_field(Keyword())
    visibility: M[str] = mapped_field(Keyword())
    group_id: M[int | None] = mapped_field(Integer())
    assignee_ids: M[list[int]] = mapped_field(Keyword(multi=True))
    updated_at: M[datetime] = mapped_field(Date())
    created_at: M[datetime] = mapped_field(Date())
    group_name: M[str] = mapped_field(Keyword())
    comment_count: M[int] = mapped_field(Integer())
    group_admin_username: M[str] = mapped_field(Keyword())
    is_active: M[bool] = mapped_field(Boolean())
    deadline: M[datetime | None] = mapped_field(Date())
    spheres: M[list[str]] = mapped_field(Keyword(multi=True))

    class Index:
        name = get_index_name("tasks_v1")
        settings: ClassVar[dict[str, Any]] = {
            "number_of_shards": 1,
            "number_of_replicas": 0,
            "analysis": RUSSIAN_ANALYZER_SETTINGS,
        }

    @classmethod
    def from_orm(cls, task: Task) -> "TaskDoc":
        title = getattr(task, "title", "") or ""
        description = getattr(task, "description", "") or ""
        status = getattr(
            task, "status", type("Enum", (), {"value": lambda s: ""})()
        ).value
        priority = getattr(
            task, "priority", type("Enum", (), {"value": lambda s: ""})()
        ).value
        difficulty = getattr(task, "difficulty", None)
        visibility = getattr(
            task, "visibility", type("Enum", (), {"value": lambda s: ""})()
        ).value
        group_id_raw = getattr(task, "group_id", None)
        group_id = int(group_id_raw) if group_id_raw is not None else None
        is_active = getattr(task, "is_active", True)
        deadline = getattr(task, "deadline", None)
        spheres = getattr(task, "spheres", [])
        assignee_ids = getattr(task, "assignee_ids", [])
        comment_count = getattr(task, "comment_count", 0)
        group_info = getattr(task, "group", None)
        group_name = group_info.name if group_info else ""
        group_admin_username = getattr(task, "group_admin_username", "")

        return cls(
            id=task.id,
            title=title,
            description=description,
            status=status,
            priority=priority,
            difficulty=difficulty,
            visibility=visibility,
            group_id=group_id,
            created_at=task.created_at,
            updated_at=task.updated_at,
            is_active=is_active,
            deadline=deadline,
            spheres=spheres,
            assignee_ids=assignee_ids,
            comment_count=comment_count,
            group_name=group_name,
            group_admin_username=group_admin_username,
        )

    def to_read_schema(self) -> TaskRead:
        """ES → Pydantic TaskRead."""
        return TaskRead.model_validate(self)
