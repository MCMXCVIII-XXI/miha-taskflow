from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.db.mixins import IdPkMixin
from app.schemas.enum import JoinRequestStatus

if TYPE_CHECKING:
    from app.models.group import UserGroup
    from app.models.task import Task
    from app.models.user import User


class JoinRequest(Base, IdPkMixin):
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("user_groups.id"), index=True)
    task_id: Mapped[int | None] = mapped_column(
        ForeignKey("tasks.id"), nullable=True, index=True
    )
    status: Mapped[JoinRequestStatus] = mapped_column(
        Enum(JoinRequestStatus),
        default=JoinRequestStatus.PENDING,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    user: Mapped["User"] = relationship("User")
    group: Mapped["UserGroup"] = relationship("UserGroup")
    task: Mapped["Task"] = relationship("Task", foreign_keys=[task_id])
    __table_args__ = (
        UniqueConstraint(
            "user_id", "group_id", "task_id", name="uq_user_group_task_join_request"
        ),
    )
