from collections.abc import Callable
from typing import Any

from fastapi import Request

from .exceptions import cache_exc


def key_builder_factory(id_field: str) -> Callable[..., str]:
    """
    Factory function to create a key builder for a given id field.

    Details:
        The key builder function uses the id field value
            from kwargs or args to construct a cache key.

    Args:
        id_field (str): The name of the field to use as the key value.

    Returns:
        Callable[..., str]: A key builder function that can be used with fastapi-cache2.
    """

    def key_builder(
        func: Callable[..., Any],
        namespace: str = "",
        request: Request | None = None,
        response: None | Any = None,
        *args: Any,
        **kwargs: Any,
    ) -> str:
        # fastapi-cache2 already includes prefix in namespace
        # namespace format: "prefix:original_namespace"

        # fastapi-cache2 packs call args into kwargs["args"] and kwargs["kwargs"]
        call_args = kwargs.get("args", ())
        call_kwargs = kwargs.get("kwargs", {})

        # 1. From kwargs (keyword arg)
        value = call_kwargs.get(id_field)

        # 2. From args (positional arg)
        if value is None and call_args:
            value = call_args[0]

        # 3. From request.path_params (HTTP endpoint)
        if value is None and request is not None:
            value = request.path_params.get(id_field)

        if not value:
            raise cache_exc.CacheNotFoundError(message=f"{id_field} not found")

        # Use namespace as-is (includes prefix from fastapi-cache2)
        return f"{namespace}:{id_field}:{value}"

    return key_builder


rbac_key = key_builder_factory("user_id")
item_key = key_builder_factory("item_id")
