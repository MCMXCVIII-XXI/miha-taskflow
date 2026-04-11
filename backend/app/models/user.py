from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.db.mixins import IdPkMixin
from app.schemas.enum import GlobalUserRole, TaskSphere

if TYPE_CHECKING:
    from .comment import Comment
    from .group import UserGroupMembership
    from .notification import Notification
    from .task import TaskAssignee


class User(Base, IdPkMixin):
    """Represents a registered user in the TaskFlow system."""

    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    first_name: Mapped[str] = mapped_column(String(50))
    last_name: Mapped[str] = mapped_column(String(50))
    patronymic: Mapped[str] = mapped_column(String(50), nullable=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[GlobalUserRole] = mapped_column(
        Enum(GlobalUserRole), default=GlobalUserRole.USER, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    notifications_sent: Mapped[list["Notification"]] = relationship(
        "Notification",
        back_populates="sender",
        foreign_keys="Notification.sender_id",
    )
    notifications_received: Mapped[list["Notification"]] = relationship(
        "Notification",
        back_populates="recipient",
        foreign_keys="Notification.recipient_id",
    )
    assigned_tasks: Mapped[list["TaskAssignee"]] = relationship(
        "TaskAssignee", back_populates="user"
    )
    comments: Mapped[list["Comment"]] = relationship("Comment", back_populates="user")
    group_memberships: Mapped[list["UserGroupMembership"]] = relationship(
        "UserGroupMembership", back_populates="user"
    )


class UserSkill(Base, IdPkMixin):
    """Tracks user progress in skill spheres with XP and leveling system."""

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    sphere: Mapped[TaskSphere] = mapped_column(Enum(TaskSphere), index=True)
    xp_total: Mapped[int] = mapped_column(Integer, default=0)
    xp_today: Mapped[int] = mapped_column(Integer, default=0)
    level: Mapped[int] = mapped_column(Integer, default=1)
    streak: Mapped[int] = mapped_column(Integer, default=0)
    last_xp_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    is_frozen: Mapped[bool] = mapped_column(Boolean, default=False)
    frozen_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    __table_args__ = (UniqueConstraint("user_id", "sphere", name="uq_user_sphere"),)
