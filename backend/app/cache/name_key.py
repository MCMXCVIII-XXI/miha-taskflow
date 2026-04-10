"""Cache key builder utilities for Redis caching.

This module provides functions to generate cache keys for different
types of cached data, ensuring consistent key naming and retrieval.
"""

from collections.abc import Callable
from typing import Any

from fastapi import Request

from .exceptions import cache_exc


def key_builder_factory(id_field: str) -> Callable[..., str]:
    """Creates a cache key builder function for a specified ID field.

    Generates a function that extracts an ID field value from various sources
    including function arguments, request parameters, or keyword arguments
    to produce consistent cache keys for FastAPI-Cache.

    Args:
        id_field (str): Name of the field to use as the key identifier

    Returns:
        Callable[..., str]: Key builder function for FastAPI-Cache integration

    Example:
        rbac_key = key_builder_factory("user_id")
        # Generates keys like "namespace:user_id:123"
    """

    def key_builder(
        func: Callable[..., Any],
        namespace: str = "",
        request: Request | None = None,
        response: None | Any = None,
        *args: Any,
        **kwargs: Any,
    ) -> str:
        """Build cache key using ID field value.

        Extracts the ID field value from various sources and constructs
        a cache key in the format: "{namespace}:{id_field}:{value}"

        Args:
            func: The decorated function
            namespace: Cache namespace prefix
            request: HTTP request object (for endpoint caching)
            response: HTTP response object
            *args: Positional arguments to the function
            **kwargs: Keyword arguments to the function

        Returns:
            str: Generated cache key

        Raises:
            cache_exc.CacheNotFoundError: When ID field value cannot be found
        """
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


# Pre-configured key builders for common use cases
rbac_key = key_builder_factory("user_id")
item_key = key_builder_factory("item_id")
