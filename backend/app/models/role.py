from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.db.mixins import IdPkMixin


class Permission(IdPkMixin, Base):
    """Permission model for Role-Based Access Control (RBAC) system."""

    name: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    resource: Mapped[str] = mapped_column(String(50), index=True)
    action: Mapped[str] = mapped_column(String(50), index=True)
    context: Mapped[str | None] = mapped_column(String(50), index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    @classmethod
    def create(
        cls,
        resource: str,
        action: str,
        context: str | None = None,
        description: str | None = None,
    ) -> "Permission":
        """Factory method to create a Permission with auto-generated name."""
        name = f"{resource}:{action}:{context}" if context else f"{resource}:{action}"
        return cls(
            resource=resource,
            action=action,
            context=context,
            name=name,
            description=description,
        )


class Role(IdPkMixin, Base):
    """Role model for Role-Based Access Control (RBAC) system."""

    name: Mapped[str] = mapped_column(unique=True, index=True)
    description: Mapped[str | None] = mapped_column()


class RolePermission(Base):
    """Association model linking roles to permissions."""

    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), primary_key=True)
    permission_id: Mapped[int] = mapped_column(
        ForeignKey("permissions.id"), primary_key=True
    )


class UserRole(IdPkMixin, Base):
    """Model representing user role assignments in specific contexts."""

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"))
    group_id: Mapped[int | None] = mapped_column(
        ForeignKey("user_groups.id"), nullable=True
    )
    task_id: Mapped[int | None] = mapped_column(ForeignKey("tasks.id"), nullable=True)
    __table_args__ = (
        UniqueConstraint(
            "user_id", "role_id", "group_id", "task_id", name="uq_user_role_group_task"
        ),
    )
