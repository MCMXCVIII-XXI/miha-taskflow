from datetime import datetime
from typing import Any, ClassVar

from elasticsearch.dsl import (
    AsyncDocument,
    Date,
    Integer,
    Keyword,
    M,
    Text,
    mapped_field,
)

from app.models import Comment
from app.schemas import CommentRead

from .utils import RUSSIAN_ANALYZER_SETTINGS, get_index_name


class CommentDoc(AsyncDocument):
    """ES Document for Comment."""

    id: M[int] = mapped_field(Integer())
    content: M[str] = mapped_field(Text(analyzer="comment_analyzer"))
    task_id: M[int] = mapped_field(Integer())
    user_id: M[int] = mapped_field(Integer())
    parent_id: M[int | None] = mapped_field(Integer())
    created_at: M[datetime] = mapped_field(Date())
    updated_at: M[datetime | None] = mapped_field(Date())
    task_title: M[str] = mapped_field(Keyword())
    username: M[str] = mapped_field(Keyword())
    task_status: M[str] = mapped_field(Keyword())

    class Index:
        name = get_index_name("comments_v1")
        settings: ClassVar[dict[str, Any]] = {
            "number_of_shards": 1,
            "number_of_replicas": 0,
            "analysis": RUSSIAN_ANALYZER_SETTINGS,
        }

    @classmethod
    def from_orm(cls, comment: Comment) -> "CommentDoc":
        """SQLAlchemy Comment → ES Document."""
        return cls(
            id=comment.id,
            content=comment.content or "",
            task_id=int(comment.task_id),
            user_id=int(comment.user_id),
            parent_id=int(comment.parent_id) if comment.parent_id else None,
            created_at=comment.created_at,
            updated_at=comment.updated_at,
            task_title=getattr(comment.task, "title", "")
            if getattr(comment, "task", None)
            else "",
            username=getattr(comment.user, "username", "")
            if getattr(comment, "user", None)
            else "",
            task_status=getattr(comment.task, "status", "")
            if getattr(comment.task, "status", None)
            else "",
        )

    def to_read_schema(self) -> CommentRead:
        """ES → Pydantic CommentRead."""
        return CommentRead.model_validate(self)
