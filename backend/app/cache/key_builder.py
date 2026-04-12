"""
Cache key builder with unified namespace handling.
==============================================================================
KEY FORMAT
==============================================================================
{env}:{lifetime}:{prefix}:{version}:{layer}:{area}:{entity}:{action}:{normalized_params}
Example:
  prod:temp:taskflow:v1:api:search:task:search:q_abc|limit_10|offset_0
==============================================================================
POSITION VALUES
==============================================================================
Position | Field      | Allowed Values
---------|------------|-------------------------------------------------
1        | env        | dev, staging, prod
2        | lifetime   | temp
3        | prefix     | taskflow
4        | version    | v1
5        | layer      | api, service, es, db
6        | area       | search, rbac, auth, xp, notification, rating
7        | entity     | task, user, group, comment, notification, rating, role, join
8        | action     | search, detail, list, create, update, delete
9        | params     | normalized query parameters
==============================================================================
NORMALIZATION RULES
==============================================================================
- '=' -> '_' (key-value separator): user_id=123 -> user_id_123
- '&' -> '|' (parameter separator): q=abc&limit=10 -> q_abc|limit_10
- Special chars (? / %) -> URL encoding: q=test? -> q_test%3F
- All lowercase: USER_ID -> user_id
- If params >50 chars -> hash (first 16 MD5 chars)
==============================================================================
EXAMPLES
==============================================================================
Search (short params):
  prod:temp:taskflow:v1:api:search:task:search:q_abc|limit_10|offset_0
Search (long params):
  prod:temp:taskflow:v1:service:search:task:search:hash_e3b0c44298fc1c14
ID-based:
  prod:temp:taskflow:v1:api:rbac:user:detail:user_id_123
==============================================================================
TTL GUIDELINES
==============================================================================
Action Type | Recommended TTL
------------|------------------
search      | 300 sec (5 min)
detail      | 1800 sec (30 min)
list        | 600 sec (10 min)
create/update/delete | Invalidate immediately
==============================================================================
"""

import hashlib
from collections.abc import Callable
from typing import Any
from urllib.parse import quote

from fastapi import Request

from .exceptions import cache_exc


class KeyBuilder:
    """Unified cache key builder following TaskFlow conventions.

    Format:
        {env}:{lifetime}:{prefix}:{version}:{layer}:{area}:{entity}:{action}:{normalized_params}

    Example:
        prod:temp:taskflow:v1:api:search:task:search:q_abc|limit_10|offset_0
    """

    ENV = ("dev", "staging", "prod")
    LIFETIME = "temp"
    PREFIX = "taskflow"
    VERSION = "v1"
    # Valid values for each position
    LAYERS = ("api", "service", "es", "db")
    AREAS = ("search", "rbac", "auth", "xp", "notification", "rating")
    ENTITIES = (
        "task",
        "user",
        "group",
        "comment",
        "notification",
        "rating",
        "role",
        "join",
    )
    ACTIONS = ("search", "detail", "list", "create", "update", "delete")

    @staticmethod
    def _normalize_namespace(namespace: str) -> str:
        """Ensure namespace ends with ':' for consistent key generation."""
        if namespace and not namespace.endswith(":"):
            return namespace + ":"
        return namespace

    @staticmethod
    def normalize_params(params: dict[str, str]) -> str:
        """Normalize parameters according to conventions.

        Rules:
        - All lowercase
        - '=' replaced with '_' (key-value)
        - '&' replaced with '|' (parameter separator)
        - Special chars (? / %) URL-encoded
        - If >50 chars, use MD5 hash (first 16 chars)
        """
        if not params:
            return ""
        normalized = {}
        for key, value in sorted(params.items()):
            key = key.lower()
            value = str(value).lower()
            # Replace separators
            value = value.replace("=", "_").replace("&", "|")
            # URL encode special characters
            value = quote(value, safe="")
            normalized[key] = value
        param_str = "|".join(f"{k}_{v}" for k, v in normalized.items())
        # Hash if too long
        if len(param_str) > 50:
            hash_val = hashlib.sha256(param_str.encode()).hexdigest()[:16]
            return f"hash_{hash_val}"
        return param_str

    def build_key(
        self,
        layer: str,
        area: str,
        entity: str,
        action: str,
        params: dict[str, str] | None = None,
        env: str | None = None,
    ) -> str:
        """Build complete cache key.

        Args:
            layer: Application layer (api, service, es, db)
            area: Functional area (search, rbac, auth, etc.)
            entity: Data entity (task, user, group, etc.)
            action: Operation type (search, detail, list, etc.)
            params: Query parameters dict
            env: Environment (dev, staging, prod)

        Returns:
            Formatted cache key string
        """
        parts = [
            env or "prod",
            self.LIFETIME,
            self.PREFIX,
            self.VERSION,
            layer,
            area,
            entity,
            action,
        ]
        key = ":".join(parts)
        if params:
            normalized = self.normalize_params(params)
            key = f"{key}:{normalized}"
        return key

    def id_key_builder(self, id_field: str) -> Callable[..., str]:
        """ID-based key builder (user_id, task_id, group_id, etc.)"""

        def builder(
            func: Callable[..., Any],
            namespace: str = "",
            request: Request | None = None,
            response: Any | None = None,
            *args: Any,
            **kwargs: Any,
        ) -> str:
            call_args = kwargs.get("args", ())
            call_kwargs = kwargs.get("kwargs", {})
            # Extract ID value
            value = call_kwargs.get(id_field)
            if value is None and call_args:
                value = call_args[0]
            if value is None and request:
                value = request.path_params.get(id_field)
            if not value:
                raise cache_exc.CacheNotFoundError(f"{id_field} not found")
            # Determine layer and area from function
            env = self._infer_env(request)
            layer = self._infer_layer(func.__module__)
            area = self._infer_area(func.__module__)
            entity = id_field.replace("_id", "")
            action = "detail"
            return self.build_key(
                layer, area, entity, action, {id_field: str(value)}, env=env
            )

        return builder

    def search_key_builder(
        self,
        func: Callable[..., Any],
        namespace: str = "",
        request: Request | None = None,
        response: Any | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> str:
        """Search query-based key builder"""
        if not request:
            raise cache_exc.CacheNotFoundError("request not found")
        # Extract search parameters
        allowed_params = ("q", "sort", "page", "size", "status", "group_id")
        params = {k: v for k, v in request.query_params.items() if k in allowed_params}
        # Determine layer and area
        env = self._infer_env(request)
        layer = self._infer_layer(func.__module__)
        area = "search"
        entity = self._infer_search_entity(request.url.path)
        action = "search"
        return self.build_key(layer, area, entity, action, params or None, env=env)

    def _infer_env(self, request: Request | None) -> str:
        """Infer environment from request."""
        if not request:
            return "prod"

        host = request.url.hostname or ""

        if "localhost" in host or "127.0.0.1" in host:
            return "dev"
        elif "staging" in host or "stage" in host:
            return "staging"
        else:
            return "prod"

    def _infer_layer(self, module: str) -> str:
        """Infer layer from function module."""
        if "api.v1.endpoints" in module:
            return "api"
        elif "service.query_db" in module:
            return "db"
        elif "es" in module:
            return "es"
        else:
            return "service"

    def _infer_area(self, module: str) -> str:
        """Infer area from function module."""
        if "search" in module:
            return "search"
        elif "rbac" in module or "permission" in module:
            return "rbac"
        elif "auth" in module:
            return "auth"
        elif "xp" in module:
            return "xp"
        elif "notification" in module:
            return "notification"
        elif "rating" in module:
            return "rating"
        else:
            return "search"

    def _infer_search_entity(self, path: str) -> str:
        """Infer entity from search endpoint path."""
        path = path.lower()
        if "task" in path:
            return "task"
        elif "user" in path:
            return "user"
        elif "group" in path:
            return "group"
        elif "comment" in path:
            return "comment"
        elif "notification" in path:
            return "notification"
        elif "rating" in path:
            return "rating"
        else:
            return "task"


# Pre-configured instances
kb = KeyBuilder()
# Ready-to-use key builders
rbac_key = kb.id_key_builder("user_id")
item_key = kb.id_key_builder("item_id")
search_key = kb.search_key_builder
