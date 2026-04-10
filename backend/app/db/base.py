"""Defines the base class for SQLAlchemy ORM models in TaskFlow.

This module provides the abstract base class that all database models inherit from.
It implements automatic table name generation using snake_case conversion from
class names and serves as the foundation for the application's data model hierarchy.
"""

from sqlalchemy.orm import DeclarativeBase, declared_attr

from app.utils import camel_to_snake


class Base(DeclarativeBase):
    """Abstract base class for all SQLAlchemy ORM models.

    Serves as the foundation for all database models in the application
    with automatic table name generation. All model classes should inherit
    from this base class.

    Attributes:
        __abstract__ (bool): Marks this as an abstract base class
    """

    __abstract__ = True

    @declared_attr.directive
    def __tablename__(cls) -> str:
        """Generates table name from class name using snake_case conversion.

        Automatically converts CamelCase class names to snake_case table names
        with 's' suffix (e.g., UserProfile -> user_profiles).

        Returns:
            str: Generated table name with 's' suffix
        """
        return f"{camel_to_snake(cls.__name__)}s"
