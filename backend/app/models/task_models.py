from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.db.mixins import IdPkMixin
from app.schemas.task_schemas import TaskPriority, TaskStatus


class TaskModel(Base, IdPkMixin):
    title: Mapped[str] = mapped_column(String(200), index=True)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus), default=TaskStatus.PENDING, index=True
    )
    priority: Mapped[TaskPriority] = mapped_column(Enum(TaskPriority), index=True)
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
    assignees: Mapped[list["TaskAssignee"]] = relationship(
        "TaskAssignee", back_populates="task", cascade="all, delete-orphan"
    )

    group: Mapped["UserGroupModel"] = relationship("UserGroup", back_populates="tasks")


class TaskAssignee(Base, IdPkMixin):
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    assigned_at: Mapped[datetime] = mapped_column(default=func.now())

    task: Mapped["TaskModel"] = relationship("TaskModel", back_populates="assignees")
    user: Mapped["UserModel"] = relationship(
        "UserModel", back_populates="assigned_tasks"
    )
