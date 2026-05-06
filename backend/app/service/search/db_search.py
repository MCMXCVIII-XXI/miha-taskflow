import inspect
from collections.abc import Awaitable, Callable
from typing import Any, Generic, TypeVar

from pydantic import BaseModel
from sqlalchemy import Select, asc, desc

from app.db import Base
from app.models import Task as TaskModel
from app.models import User as UserModel
from app.models import UserGroup as UserGroupModel
from app.schemas import (
    TaskRead,
    TaskSearch,
    UserGroupRead,
    UserGroupSearch,
    UserRead,
    UserSearch,
)

from ..exceptions import search_exc

ModelT = TypeVar("ModelT", bound=Base)
SchemaT = TypeVar("SchemaT", bound=BaseModel)


class SearchParameters(Generic[ModelT]):
    """Generic search decorator configuration for SQLAlchemy models.

    Maps Pydantic search/sort schemas to SQLAlchemy model fields and provides
    automatic LIKE filtering, multi-field sorting (max 3), and pagination.
    Transforms Select[tuple[ModelT]] to list[SchemaT] automatically.

    Attributes:
        search_schema: Pydantic model for search parameters
        sort_schema: Pydantic model for sort parameters
        model: SQLAlchemy model class
        schema_class: Pydantic schema class for serialization
        search_fields: Field to column mapping
        sort_fields: Sort field to column mapping
        MAX_SORT_FIELDS: Maximum number of sort fields allowed (3)

    Example:
        ```python
        user_search = SearchParameters(UserSearch, UserSearch, UserModel, UserRead)
        ```
    """

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
        """Decorate service method to handle search/sort/pagination.

        Injects search/sort/limit/offset parameters automatically to provide
        a zero-boilerplate search API for service methods.

        Args:
            function: Base query method to decorate

        Returns:
            Callable: Decorated function that returns list[SchemaT]

        Example:
            ```python
            @user_search
            async def search_users(self):
                return self._user_repo.all_select(is_active=True)
            ```
        """

        async def decorated_function(
            service: Any,
            *args: Any,
            **kwargs: Any,
        ) -> list[SchemaT]:
            search_param = kwargs.pop("search", None)
            sort_param = kwargs.pop("sort", None)
            limit_param = kwargs.pop("limit", 10)
            offset_param = kwargs.pop("offset", 0)
            current_user = kwargs.pop("current_user", None)

            if current_user is None and args:
                current_user = args[0]
                args = args[1:]

            call_kwargs: dict[str, Any] = {
                "search": search_param,
                "sort": sort_param,
                "limit": limit_param,
                "offset": offset_param,
            }
            if "current_user" in inspect.signature(function).parameters:
                call_kwargs["current_user"] = current_user
            base_query: Select[tuple[ModelT, ...]] = await function(
                service,
                *args,
                **call_kwargs,
                **kwargs,
            )

            query = base_query
            if search_param:
                query = self._apply_search(query, search_param)
            if sort_param:
                query = self._apply_sort(query, sort_param)

            query = query.limit(limit_param).offset(offset_param)
            result = await service._db.scalars(query)
            models = result.all()

            return [self.schema_class.model_validate(model) for model in models]  # type: ignore[misc]

        decorated_function.__name__ = function.__name__
        decorated_function.__doc__ = function.__doc__

        return decorated_function

    def _apply_search(
        self, query: Select[tuple[ModelT, ...]], search: BaseModel
    ) -> Select[tuple[ModelT, ...]]:
        """Apply dynamic search filters (LIKE/==).

        Applies string fields with ilike("%value%") and others with exact match.
        Performs multi-field AND filtering from model_dump(exclude_none=True).
        Validates field existence before applying filters.

        Args:
            query: Base query to apply filters to
            search: Search filters as Pydantic model

        Returns:
            Select[tuple[ModelT,...]]: Filtered query

        Raises:
            search_exc.InvalidFieldError: When search field doesn't exist in model

        Example:
            ```python
            query = search_params._apply_search(base_query, UserSearch(username="john"))
            # → query.filter(User.username.ilike("%john%"))
            ```
        """
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
        """Apply multi-field sorting (ASC/DESC).

        Applies sorting with maximum 3 sort fields (MAX_SORT_FIELDS=3).
        Uses boolean direction mapping to asc/desc. Chains multiple order_by() calls.

        Args:
            query: Base query to apply sorting to
            sort: Sort directions as Pydantic model {field: True/False}

        Returns:
            Select[tuple[ModelT,...]]: Ordered query

        Raises:
            search_exc.TooManySortFieldsError: When more than 3 sort fields are provided
            search_exc.InvalidFieldError: When sort field doesn't exist in model

        Example:
            ```python
            query = search_params._apply_sort(
                        base_query,
                        UserSearch(sort={"name": True})
                        )
            # → query.order_by(desc(User.name))
            ```
        """
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
