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

from app.core.log import logging
from app.models import UserGroup
from app.schemas import UserGroupRead

from .utils import RUSSIAN_ANALYZER_SETTINGS, get_index_name

logger = logging.get_logger(__name__)


class UserGroupDoc(AsyncDocument):
    """ES Document for UserGroup."""

    id: M[int] = mapped_field(Integer())
    name: M[str] = mapped_field(Text(boost=3))
    description: M[str | None] = mapped_field(Text(boost=2))
    admin_id: M[int] = mapped_field(Integer())
    visibility: M[str] = mapped_field(Keyword())
    join_policy: M[str] = mapped_field(Keyword())
    created_at: M[datetime] = mapped_field(Date())
    parent_group_id: M[int | None] = mapped_field(Integer())
    level: M[int] = mapped_field(Integer())
    is_active: M[bool] = mapped_field(Boolean())
    updated_at: M[datetime | None] = mapped_field(Date())
    invite_policy: M[str] = mapped_field(Keyword())
    admin_username: M[str] = mapped_field(Keyword())
    task_count: M[int] = mapped_field(Integer())
    member_count: M[int] = mapped_field(Integer())
    sub_group_ids: M[list[int]] = mapped_field(Keyword(multi=True))
    task_ids: M[list[int]] = mapped_field(Keyword(multi=True))

    class Index:
        name = get_index_name("groups_v1")
        settings: ClassVar[dict[str, Any]] = {
            "number_of_shards": 1,
            "number_of_replicas": 0,
            "analysis": RUSSIAN_ANALYZER_SETTINGS,
        }

    @classmethod
    def from_orm(cls, group: UserGroup) -> "UserGroupDoc":
        admin = getattr(group, "admin", None)
        sub_group_ids = getattr(group, "sub_group_ids", []) or []
        task_ids = getattr(group, "task_ids", []) or []
        user_count = getattr(group, "member_count", 0) or 0
        task_count = getattr(group, "task_count", 0) or 0

        return cls(
            id=group.id,
            name=group.name or "",
            description=group.description or "",
            admin_id=group.admin_id,
            visibility=group.visibility.value,
            join_policy=group.join_policy.value,
            created_at=group.created_at,
            parent_group_id=int(group.parent_group_id)
            if group.parent_group_id
            else None,
            level=group.level or 0,
            is_active=getattr(group, "is_active", True),
            updated_at=group.updated_at,
            invite_policy=group.invite_policy.value,
            admin_username=getattr(admin, "username", "") if admin else "",
            task_count=task_count,
            member_count=user_count,
            sub_group_ids=sub_group_ids,
            task_ids=task_ids,
        )

    def to_read_schema(self) -> UserGroupRead:
        """ES → Pydantic UserGroupRead."""
        return UserGroupRead.model_validate(self)
