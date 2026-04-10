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
        """
        Convert Task ORM model to TaskDoc for Elasticsearch.

        Note: For optimal performance, task should be loaded with:
        select(Task).options(
            joinedload(Task.group),
            selectinload(Task.assignees),
            selectinload(Task.comments)
        )
        """
        # Безопасное извлечение связанных данных
        group_info = getattr(task, "group", None)
        group_name = group_info.name if group_info else ""

        assignees = getattr(task, "assignees", [])
        assignee_ids = [a.user_id for a in assignees] if assignees else []

        comments = getattr(task, "comments", [])
        comment_count = len(comments) if comments else 0

        spheres_data = task.spheres or []
        spheres = []
        for s in spheres_data:
            if isinstance(s, dict) and "sphere" in s:
                spheres.append(s["sphere"])
            elif hasattr(s, "sphere"):  # Если это объект модели
                spheres.append(s.sphere)

        return cls(
            id=task.id,
            title=task.title or "",
            description=task.description or "",
            status=task.status.value,
            priority=task.priority.value,
            difficulty=str(task.difficulty.value) if task.difficulty else None,
            visibility=task.visibility.value,
            group_id=int(task.group_id) if task.group_id else None,
            assignee_ids=assignee_ids,
            created_at=task.created_at,
            updated_at=task.updated_at,
            group_name=group_name,
            comment_count=comment_count,
            group_admin_username=getattr(group_info, "admin_username", "")
            if group_info
            else "",
            is_active=getattr(task, "is_active", True),
            deadline=task.deadline,
            spheres=spheres,
        )

    def to_read_schema(self) -> TaskRead:
        """ES → Pydantic TaskRead."""
        return TaskRead.model_validate(self)
