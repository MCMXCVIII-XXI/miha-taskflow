from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Any, Generic, TypeVar

from pydantic import BaseModel
from sqlalchemy import Select, asc, desc

from app.db import Base
from app.models import Task as TaskModel
from app.models import User as UserModel
from app.models import UserGroup as UserGroupModel
from app.schemas.group_schemas import UserGroupRead
from app.schemas.search_schemas import (
    TaskSearch,
    UserGroupSearch,
    UserSearch,
)
from app.schemas.task_schemas import TaskRead
from app.schemas.user_schemas import UserRead

from .exceptions import search_exc

ModelT = TypeVar("ModelT", bound=Base)
SchemaT = TypeVar("SchemaT", bound=BaseModel)


class SearchParameters(Generic[ModelT]):
    MAX_SORT_FIELDS = 3

    def __init__(
        self,
        search_schema: type[BaseModel],
        sort_schema: type[BaseModel],
        model: type[ModelT],
        schema_class: type[SchemaT],
    ):
        self.search_schema = search_schema
        self.sort_schema = sort_schema
        self.model = model
        self.schema_class = schema_class

        self.search_fields = {
            field_name: getattr(self.model, field_name)
            for field_name, _ in self.search_schema.model_fields.items()
        }
        self.sort_fields = {
            field_name: getattr(self.model, field_name)
            for field_name, _ in self.sort_schema.model_fields.items()
        }

    def __call__(
        self, function: Callable[..., Any]
    ) -> Callable[..., Awaitable[list[SchemaT]]]:
        @wraps(function)
        async def decorated_function(
            service: Any,
            *args: Any,
            search: BaseModel | None = None,
            sort: BaseModel | None = None,
            limit: int = 10,
            offset: int = 0,
            **kwargs: Any,
        ) -> list[SchemaT]:
            base_query: Select[tuple[ModelT, ...]] = await function(
                service, *args, **kwargs
            )

            query = base_query
            if search:
                query = self._apply_search(query, search)
            if sort:
                query = self._apply_sort(query, sort)

            query = query.limit(limit).offset(offset)
            result = await service._db.scalars(query)
            models = result.all()

            # MyPy: SchemaT variance between __init__ and decorated_function contexts
            return [self.schema_class.model_validate(model) for model in models]  # type: ignore[misc]

        return decorated_function

    def _apply_search(
        self, query: Select[tuple[ModelT, ...]], search: BaseModel
    ) -> Select[tuple[ModelT, ...]]:
        search_dict = search.model_dump(exclude_none=True)

        for field_name, value in search_dict.items():
            if field_name not in self.search_fields:
                raise search_exc.InvalidFieldError(
                    f"Invalid search field: {field_name}"
                )

            model_field = self.search_fields[field_name]
            if isinstance(value, str):
                query = query.filter(model_field.ilike(f"%{value}%"))
            else:
                query = query.filter(model_field == value)
        return query

    def _apply_sort(
        self, query: Select[tuple[ModelT, ...]], sort: BaseModel
    ) -> Select[tuple[ModelT, ...]]:
        sort_dict = sort.model_dump(exclude_none=True)

        if len(sort_dict) > self.MAX_SORT_FIELDS:
            raise search_exc.TooManySortFieldsError(
                f"Too many sort fields: {len(sort_dict)} > {self.MAX_SORT_FIELDS}"
            )

        for field_name, direction in sort_dict.items():
            if field_name not in self.sort_fields:
                raise search_exc.InvalidFieldError(f"Invalid sort field: {field_name}")

            model_field = self.sort_fields[field_name]
            order = desc(model_field) if direction else asc(model_field)
            query = query.order_by(order)
        return query


task_search = SearchParameters(
    search_schema=TaskSearch,
    sort_schema=TaskSearch,
    model=TaskModel,
    schema_class=TaskRead,
)

user_search = SearchParameters(
    search_schema=UserSearch,
    sort_schema=UserSearch,
    model=UserModel,
    schema_class=UserRead,
)

group_search = SearchParameters(
    search_schema=UserGroupSearch,
    sort_schema=UserGroupSearch,
    model=UserGroupModel,
    schema_class=UserGroupRead,
)
