from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.db.mixins import IdPkMixin


class UserGroupModel(Base, IdPkMixin):
    name: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    admin_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    tasks: Mapped[list["TaskModel"]] = relationship(
        "Task", back_populates="group", cascade="all, delete-orphan"
    )
    users: Mapped[list["UserGroupMembershipModel"]] = relationship(
        "UserGroupMembershipModel", back_populates="group"
    )


class UserGroupMembershipModel(Base, IdPkMixin):
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    group_id: Mapped[int] = mapped_column(ForeignKey("user_groups.id"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    user: Mapped["UserModel"] = relationship(
        "UserModel", back_populates="group_memberships"
    )
    group: Mapped["UserGroupModel"] = relationship(
        "UserGroupModel", back_populates="users"
    )
