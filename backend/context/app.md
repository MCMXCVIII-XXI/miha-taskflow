# app_context.md

## 1. Purpose of the directory
The `app/` directory is the core application layer of the TaskFlow project. It contains all the business logic, data models, API endpoints, and infrastructure integrations.

## 2. Typical contents
- `api/` - REST API routes and endpoint definitions (v1)
- `background/` - Celery background tasks, beat schedule, signals
- `cache/` - Redis caching implementation and utilities
- `cli/` - Command-line interface tools
- `core/` - Core application configuration, logging, security, permissions
- `db/` - Database models, helpers, and connection management
- `documents/` - Elasticsearch document definitions for indexing
- `es/` - Elasticsearch integration and search functionality
- `models/` - SQLAlchemy database models
- `repositories/` - Data access layer (repositories pattern)
- `schemas/` - Pydantic data validation schemas
- `service/` - Business logic implementations
- `utils/` - Shared utility functions

## 3. How key modules work
- `api/v1/endpoints/`: Contains API routers that define HTTP endpoints and map them to service methods.
- `service/`: Contains business logic organized by domain entities (tasks, users, groups, etc.), including transaction services for atomic operations.
- `models/`: SQLAlchemy ORM models that represent database tables.
- `schemas/`: Pydantic models for request/response validation.
- `db/`: Database connection and session management.
- `es/`: Elasticsearch client and indexing functionality.
- `cache/`: Redis caching for performance optimization.
- `background/`: Celery tasks for async processing, beat schedule, signals.
- `cli/`: Management commands for database operations, reindexing.

## 4. Request flow
1. Request arrives at FastAPI through endpoint in `api/`
2. API router validates request using schemas from `schemas/`
3. API handler calls service from `service/`
4. Service performs business logic and interacts with:
   - Database through repositories in `repositories/`
   - Elasticsearch through `es/` and documents in `documents/`
   - Redis cache through `cache/`
   - Background tasks through `background/`
5. Service returns processed data to API handler
6. API handler formats response using schemas

## 5. Summary
The `app/` directory contains all core functionality organized by architectural layers. Key additions: `background/` for async tasks, `cli/` for management commands, `repositories/` for data access layer.
