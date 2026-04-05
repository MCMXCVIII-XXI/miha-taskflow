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
from app.schemas.enum import GroupVisibility, InvitePolicy, JoinPolicy

if TYPE_CHECKING:
    from .task import Task
    from .user import User


class UserGroup(Base, IdPkMixin):
    name: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    admin_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    visibility: Mapped[GroupVisibility] = mapped_column(
        Enum(GroupVisibility), default=GroupVisibility.PUBLIC, index=True
    )
    join_policy: Mapped[JoinPolicy] = mapped_column(
        Enum(JoinPolicy), default=JoinPolicy.OPEN, index=True
    )
    parent_group_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("user_groups.id"), nullable=True, index=True
    )
    level: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    invite_policy: Mapped[InvitePolicy] = mapped_column(
        Enum(InvitePolicy),
        default=InvitePolicy.ADMIN_ONLY,
        index=True,
    )
    tasks: Mapped[list["Task"]] = relationship(
        "Task", back_populates="group", cascade="all, delete-orphan"
    )
    users: Mapped[list["UserGroupMembership"]] = relationship(
        "UserGroupMembership", back_populates="group"
    )
    parent_group: Mapped["UserGroup"] = relationship(
        "UserGroup",
        remote_side="UserGroup.id",
        back_populates="subgroups",
        foreign_keys=[parent_group_id],
    )
    subgroups: Mapped[list["UserGroup"]] = relationship(
        "UserGroup", back_populates="parent_group", foreign_keys=[parent_group_id]
    )


class UserGroupMembership(Base, IdPkMixin):
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    group_id: Mapped[int] = mapped_column(ForeignKey("user_groups.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    user: Mapped["User"] = relationship("User", back_populates="group_memberships")
    group: Mapped["UserGroup"] = relationship("UserGroup", back_populates="users")

    __table_args__ = (
        UniqueConstraint("user_id", "group_id", name="uq_user_group_membership"),
    )
