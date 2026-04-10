"""Provides auto-incrementing integer primary key for SQLAlchemy ORM models.

This module implements a reusable mixin that adds a standard integer primary key
field to database models. Follows common database conventions for primary key
naming and automatic generation.
"""

from sqlalchemy.orm import Mapped, mapped_column


class IdPkMixin:
    """Adds auto-incrementing integer primary key to SQLAlchemy ORM models.

    Provides a standard 'id' field configured as an auto-incrementing integer
    primary key that can be inherited by any database model class.

    Attributes:
        id (Mapped[int]): Auto-incrementing integer primary key field
    """

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
