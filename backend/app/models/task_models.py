from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.db.mixins import IdPkMixin
from app.schemas.task_schemas import TaskPriority, TaskStatus


class Task(Base, IdPkMixin):
    title: Mapped[str] = mapped_column(String(200), index=True)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    status: Mapped[TaskStatus] = mapped_column(Enum(TaskStatus), index=True)
    priority: Mapped[TaskPriority] = mapped_column(Enum(TaskPriority), index=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    group_id: Mapped[int | None] = mapped_column(
        ForeignKey("user_groups.id"), index=True
    )

    group: Mapped["UserGroup"] = relationship("UserGroup", back_populates="tasks")
    owner: Mapped["User"] = relationship("User", back_populates="tasks")
