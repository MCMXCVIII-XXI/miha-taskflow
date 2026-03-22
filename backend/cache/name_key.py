from collections.abc import Callable
from typing import Any

from fastapi import Request
from fastapi_cache import FastAPICache


def item_key_builder(
    func: Callable,
    namespace: str = "",
    request: Request | None = None,
    response: None | Any = None,
    *args: Any,
    **kwargs: Any,
) -> str:
    """Custom key builder for endpoints"""
    prefix = FastAPICache.get_prefix()

    item_id = None
    if request is not None:
        item_id = request.path_params.get("item_id")

    if item_id is None:
        item_id = kwargs.get("item_id") or (args[0] if args else None)

    if not item_id:
        raise ValueError("item_id not found in path_params/kwargs/args")

    return f"{prefix}:{namespace}:item:{item_id}"
