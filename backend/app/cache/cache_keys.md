# Redis Cache Key Conventions

## Overview

This document defines the naming conventions and format for Redis cache keys in the **TaskFlow** application. These conventions ensure **consistency, readability, and efficient key management** across all caching layers.

## Key Format


- `{env}:{lifetime}:{prefix}:{version}:{layer}:{area}:{entity}:{action}:{normalized_params}`

## Full Specification

| Position | Field              | Description                                     |
|---------|--------------------|-------------------------------------------------|
| 1       | `env`              | Environment prefix                              |
| 2       | `lifetime`         | Cache type                                      |
| 3       | `prefix`           | Application name                                |
| 4       | `version`          | API version                                     |
| 5       | `layer`            | Application layer                               |
| 6       | `area`             | Functional area                                 |
| 7       | `entity`           | Data entity                                     |
| 8       | `action`           | Operation type                                  |
| 9       | `normalized_params`| Request parameters (normalized)                 |

---

## Examples

### Search Endpoints

- `prod:temp:taskflow:v1:api:search:task:search:q_abc|limit_10|offset_0`
- `prod:temp:taskflow:v1:api:search:user:search:role_admin|limit_5`
- `prod:temp:taskflow:v1:service:search:group:search:visibility_public|limit_20`

### Long Search Query (hashed)

- `prod:temp:taskflow:v1:service:search:task:search:hash_e3b0c44298fc1c14`

### ID-based Endpoints

- `prod:temp:taskflow:v1:api:rbac:user:detail:user_id_123`
- `prod:temp:taskflow:v1:api:auth:session:detail:session_id_abc`
- `prod:temp:taskflow:v1:api:rbac:group:detail:group_id_456`

### With URL-encoded special characters

- `prod:temp:taskflow:v1:api:auth:session:detail:token_abc%3Fx%3D123`

---

## Normalization Rules

### Character Replacements

- `=` → `_`  
- `&` → `|`  
- Special chars (`?`, `/`, `%`, spaces) — URL-encoded via `quote(value, safe="")`.

### Case Handling

All parameters must be converted to lowercase.

**Example:**  
`USER_ID=123` → `user_id_123`.

### Long Parameter Handling

If `normalized_params` exceeds **50 characters**, use an MD5 hash (first **16 characters**).

**Example:**  
`q_very_long_query_string_that_exceeds_fifty_characters` → `hash_e3b0c44298fc1c14`.

---

## Layer Values (Position 5)

| Layer   | Description                          |
|---------|--------------------------------------|
| `api`   | API endpoints (public interface)     |
| `service` | Service layer (business logic)    |
| `es`    | Elasticsearch operations             |
| `db`    | Database layer                       |

---

## Area Values (Position 6)

| Area         | Description                      |
|--------------|----------------------------------|
| `search`     | Search operations                |
| `rbac`       | Permission checks                |
| `auth`       | Authentication                   |
| `xp`         | Experience / progress            |
| `notification`| Notifications                   |
| `rating`     | Ratings                          |

---

## Entity Values (Position 7)

- `task`
- `user`
- `group`
- `comment`
- `notification`
- `rating`
- `role`
- `join`

---

## Action Values (Position 8)

- `search`
- `detail`
- `list`
- `create`
- `update`
- `delete`

---

## TTL Guidelines

Always set TTL explicitly when writing to Redis.

| Action Type            | Recommended TTL (seconds) |
|-------------------------|---------------------------|
| `search`                | 300–900 (5–15 minutes)    |
| `detail`                | 1800 (30 minutes)         |
| `list`                  | 600–1200 (10–20 minutes)  |
| `create` / `update` / `delete` | 0 (no caching, only invalidation) |

**Example in Python (FastAPI context):**

```python
# 5-minute TTL for search
await redis.setex(key, 900, value)
```

---

## Environment Prefix

Always include the environment prefix to avoid conflicts when sharing Redis instances.

| Environment   |
|---------------|
| `dev`         |
| `staging`     |
| `prod`        |

---

## Key Builder Implementation (Python)

```python
import hashlib
from urllib.parse import quote


class CacheKeyBuilder:
    ENV = "prod"
    LIFETIME = "temp"
    PREFIX = "taskflow"
    VERSION = "v1"

    @staticmethod
    def normalize_params(params: dict) -> str:
        """Normalize parameters according to conventions."""
        normalized = {}
        for key, value in sorted(params.items()):
            key = key.lower()
            value = str(value).lower()
            # Replace special characters
            value = value.replace("=", "_").replace("&", "|")
            # URL encode special chars
            value = quote(value, safe="")
            normalized[key] = value

        param_str = "|".join(f"{k}_{v}" for k, v in normalized.items())

        # Hash if too long
        if len(param_str) > 50:
            hash_val = hashlib.md5(param_str.encode()).hexdigest()[:16]
            return f"hash_{hash_val}"

        return param_str

    def build_key(
        self,
        layer: str,
        area: str,
        entity: str,
        action: str,
        params: dict | None = None,
    ) -> str:
        """Build cache key."""
        parts = [
            self.ENV,
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
```

### Usage

```python
builder = CacheKeyBuilder()

# Search key
key = builder.build_key(
    layer="api",
    area="search",
    entity="task",
    action="search",
    params={"q": "abc", "limit": "10", "offset": "0"},
)
# Result: prod:temp:taskflow:v1:api:search:task:search:q_abc|limit_10|offset_0

# Detail key
key = builder.build_key(
    layer="api",
    area="rbac",
    entity="user",
    action="detail",
    params={"user_id": "123"},
)
# Result: prod:temp:taskflow:v1:api:rbac:user:detail:user_id_123
```

---

## Cache Invalidation Patterns

### Invalidate by Layer

```python
# Clear all API layer cache
await redis.execute("SCAN", 0, "MATCH", "prod:temp:taskflow:v1:api:*")
```

### Invalidate by Area

```python
# Clear all search cache
await redis.execute("SCAN", 0, "MATCH", "prod:temp:taskflow:v1:*:search:*")
```

### Invalidate by Entity

```python
# Clear all task cache
await redis.execute("SCAN", 0, "MATCH", "prod:temp:taskflow:v1:*:*:task:*")
```

### Invalidate All

```python
# Clear entire application cache
await redis.execute("SCAN", 0, "MATCH", "prod:temp:taskflow:v1:*")
```

---

## Best Practices

- Always use lowercase for all key components.
- Include environment prefix to prevent cross‑environment conflicts.
- Use consistent delimiter conventions:
  - `:` — hierarchy,
  - `_` — key‑value separators,
  - `|` — parameter separators in `normalized_params`.
- Set appropriate TTL for each cache type.
- Hash long parameters to keep keys manageable.
- Document TTL expectations in code comments.
- Use wildcards carefully in `KEYS` / `SCAN` patterns in production.
- Monitor key sizes in Redis memory.

---

## Migration from Legacy Formats

If migrating from older key formats:

- Increment version in prefix: `v1` → `v2`.
- Run a migration script to rename keys.
- Set a **short TTL** during the transition period.
- Monitor **cache hit rates** after migration.

---
