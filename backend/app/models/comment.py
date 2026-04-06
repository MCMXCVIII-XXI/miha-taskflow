from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    ForeignKey,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.db.mixins import IdPkMixin

if TYPE_CHECKING:
    from .task import Task
    from .user import User


class Comment(Base, IdPkMixin):
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    content: Mapped[str] = mapped_column(String(255))
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("comments.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    task: Mapped["Task"] = relationship("Task", back_populates="comments")
    user: Mapped["User"] = relationship("User", back_populates="comments")
