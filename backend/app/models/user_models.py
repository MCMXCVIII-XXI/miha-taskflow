from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.db.mixins import IdPkMixin
from app.schemas.user_schemas import UserRole


class UserModel(Base, IdPkMixin):
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    first_name: Mapped[str] = mapped_column(String(50))
    last_name: Mapped[str] = mapped_column(String(50))
    patronymic: Mapped[str] = mapped_column(String(50), nullable=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole), default=UserRole.MEMBER, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    admin_groups: Mapped[list["UserGroupMode"]] = relationship(
        "UserGroup", foreign_keys="UserGroup.admin_id"
    )
    assigned_tasks: Mapped[list["TaskAssignee"]] = relationship(
        "TaskAssignee", back_populates="user"
    )
    group_memberships: Mapped[list["UserGroupMembership"]] = relationship(
        "UserGroupMembership", back_populates="user"
    )
