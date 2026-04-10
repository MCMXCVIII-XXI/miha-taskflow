# app_context.md

## 1. Purpose of the directory
The `app/` directory is the core application layer of the TaskFlow project. It contains all the business logic, data models, API endpoints, and infrastructure integrations. This directory follows a modular architecture pattern where each subdirectory represents a distinct layer or concern of the application.

## 2. Typical contents
- `api/` - REST API routes and endpoint definitions
- `cache/` - Redis caching implementation and utilities
- `core/` - Core application configuration, logging, and shared utilities
- `db/` - Database models, helpers, and connection management
- `es/` - Elasticsearch integration and search functionality
- `indexes/` - Elasticsearch document definitions
- `models/` - SQLAlchemy database models
- `schemas/` - Pydantic data validation schemas
- `service/` - Business logic implementations
- `utils/` - Shared utility functions

## 3. How key modules work
- `main.py`: The application entry point that initializes FastAPI, sets up middleware, exception handlers, and connects all components together.
- `api/`: Contains API routers that define HTTP endpoints and map them to service methods.
- `service/`: Contains business logic organized by domain entities (tasks, users, groups, etc.).
- `models/`: SQLAlchemy ORM models that represent database tables.
- `schemas/`: Pydantic models for request/response validation and serialization.
- `db/`: Database connection and session management utilities.
- `es/`: Elasticsearch client and indexing functionality.
- `cache/`: Redis caching implementation for performance optimization.

## 4. Request flow and integration
A typical HTTP request flows through the application as follows:
1. Request arrives at FastAPI through an endpoint in `api/`
2. API router validates the request using schemas from `schemas/`
3. API handler calls appropriate service from `service/`
4. Service performs business logic and interacts with:
   - Database through models in `models/` and helpers in `db/`
   - Elasticsearch through utilities in `es/` and documents in `indexes/`
   - Redis cache through implementations in `cache/`
5. Service returns processed data to API handler
6. API handler formats response using schemas from `schemas/`
7. Response is sent back to client

## 5. Summary
The `app/` directory is the heart of the TaskFlow application, containing all core functionality organized by architectural layers. It orchestrates interactions between the database, Elasticsearch, Redis cache, and business logic to deliver task management features. Each subdirectory has a specific responsibility, following separation of concerns principles.