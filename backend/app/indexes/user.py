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

from app.models import User
from app.schemas import UserRead
from app.schemas.enum import GlobalUserRole

from .utils import RUSSIAN_ANALYZER_SETTINGS, get_index_name


class UserDoc(AsyncDocument):
    """Elasticsearch document structure for user full-text search."""

    id: M[int] = mapped_field(Integer())
    username: M[str] = mapped_field(Keyword())
    first_name: M[str] = mapped_field(Text(analyzer="standard"))
    last_name: M[str] = mapped_field(Text(analyzer="standard"))
    patronymic: M[str] = mapped_field(Text(analyzer="standard"))
    email: M[str] = mapped_field(Keyword())
    role: M[str] = mapped_field(Keyword())
    created_at: M[datetime] = mapped_field(Date())
    updated_at: M[datetime | None] = mapped_field(Date())
    notification_ids: M[list[str]] = mapped_field(Keyword(multi=True))
    assigned_task_ids: M[list[str]] = mapped_field(Keyword(multi=True))
    comment_ids: M[list[str]] = mapped_field(Keyword(multi=True))
    group_ids: M[list[str]] = mapped_field(Keyword(multi=True))
    admin_group_ids: M[list[str]] = mapped_field(Keyword(multi=True))
    member_group_ids: M[list[str]] = mapped_field(Keyword(multi=True))
    is_active: M[bool] = mapped_field(Boolean(), default=True)

    class Index:
        name = get_index_name("users_v1")
        settings: ClassVar[dict[str, Any]] = {
            "number_of_shards": 1,
            "number_of_replicas": 0,
            "analysis": RUSSIAN_ANALYZER_SETTINGS,
        }

    @classmethod
    def from_orm(cls, user: User) -> "UserDoc":
        """SQLAlchemy User → ES Document."""
        return cls(
            id=user.id,
            username=user.username or "",
            first_name=user.first_name or "",
            last_name=user.last_name or "",
            patronymic=getattr(user, "patronymic", "") or "",
            email=user.email or "",
            role=(
                user.role.value
                if hasattr(user, "role") and user.role
                else GlobalUserRole.USER.value
            ),
            created_at=user.created_at,
            updated_at=user.updated_at,
            is_active=getattr(user, "is_active", True),
            notification_ids=[],
            assigned_task_ids=[],
            comment_ids=[],
            group_ids=[],
            admin_group_ids=[],
            member_group_ids=cls._get_member_groups(user),
        )

    @classmethod
    def _get_member_groups(cls, user: User) -> list[str]:
        """Helper: member groups из memberships."""
        return [
            str(gm.group_id)
            for gm in getattr(user, "group_memberships", [])
            if gm and gm.group_id and not getattr(gm, "is_admin", False)
        ]

    def to_read_schema(self) -> UserRead:
        """ES → Pydantic UserRead."""
        return UserRead.model_validate(self)
