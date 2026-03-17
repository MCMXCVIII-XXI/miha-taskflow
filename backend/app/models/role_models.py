from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.schema import UniqueConstraint

from app.db import Base
from app.db.mixins import IdPkMixin


class Permission(IdPkMixin, Base):
    name: Mapped[str] = mapped_column(unique=True, index=True)
    resource: Mapped[str] = mapped_column(index=True)
    action: Mapped[str] = mapped_column(index=True)
    description: Mapped[str | None] = mapped_column()


class Role(IdPkMixin, Base):
    name: Mapped[str] = mapped_column(unique=True, index=True)
    description: Mapped[str | None] = mapped_column()


class RolePermission(Base):
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), primary_key=True)
    permission_id: Mapped[int] = mapped_column(
        ForeignKey("permissions.id"), primary_key=True
    )


class UserRole(Base):
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), primary_key=True)
    group_id: Mapped[int | None] = mapped_column(
        ForeignKey("user_groups.id"), index=True, nullable=True
    )
    __table_args__ = (
        UniqueConstraint("user_id", "role_id", "group_id", name="uq_user_role_group"),
    )
