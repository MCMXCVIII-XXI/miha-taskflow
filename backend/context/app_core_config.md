# app_core_config.md

## 1. Purpose of the directory
The `app/core/config/` directory contains configuration settings for all external services and internal components of TaskFlow. Uses Pydantic Settings pattern to manage environment variables.

## 2. Typical contents
- `__init__.py` - Exports all setting objects and creates their instances (singletons).
- `db.py` - `DBSettings`: PostgreSQL connection settings (URL, pool size, SQL logging).
- `cache.py` - `CacheSettings`: Redis settings (URL, timeouts, connection count).
- `security.py` - `SecuritySettings`: CORS and security settings.
- `logging.py` - `LoggingSettings`: Logging parameters (level, format).
- `token.py` - `TokenSettings`: JWT settings (secret, algorithm, lifetime).
- `es.py` - `ESSettings`: Elasticsearch settings (hosts, timeouts).
- `sse.py` - `SSESettings`: Server-Sent Events settings.
- `celery.py` - `CelerySettings`: Celery worker settings.

## 3. How key modules work
- `DBSettings`:
  - Input: Environment variables with `DB_` prefix.
  - Output: Object with connection parameters.
  - What it does: Configures SQLAlchemy engine.
  - How it interacts: Used in `app/db/` for DB initialization.

- `CacheSettings`:
  - Input: Environment variables with `CACHE_` prefix.
  - Output: Redis parameters.
  - What it does: Configures Redis connection pool.
  - How it interacts: Used in `app/cache/`.

## 4. Data flow and integration
1. On application startup, settings are imported from `__init__.py`.
2. Pydantic reads `.env` file and environment variables.
3. Setting instances are created (e.g., `db_settings`).
4. These objects are used in helpers and services to initialize clients.

## 5. Summary
Centralized storage for all project configurations, allowing easy environment-specific changes via environment variables.
