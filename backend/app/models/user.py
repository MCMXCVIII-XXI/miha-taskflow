from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.db.mixins import IdPkMixin
from app.schemas import GlobalUserRole

if TYPE_CHECKING:
    from .group import UserGroupMembership
    from .task import TaskAssignee


class User(Base, IdPkMixin):
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
    assigned_tasks: Mapped[list["TaskAssignee"]] = relationship(
        "TaskAssignee", back_populates="user"
    )
    group_memberships: Mapped[list["UserGroupMembership"]] = relationship(
        "UserGroupMembership", back_populates="user"
    )
