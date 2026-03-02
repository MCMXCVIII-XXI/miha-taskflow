from sqlalchemy.orm import DeclarativeBase, declared_attr

from app.utils import camel_to_snake


class Base(DeclarativeBase):
    __abstract__ = True

    @declared_attr.directive
    def __tablename__(cls) -> str:
        return f"{camel_to_snake(cls.__name__)}s"
