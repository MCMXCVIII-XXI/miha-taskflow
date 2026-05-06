# app_core_context.md

## 1. Purpose of the directory
The `app/core/` directory serves as the foundational infrastructure layer of the TaskFlow application. It contains core configurations, security implementations, logging utilities, middleware components, permission system, and shared utilities used across all other layers.

## 2. Typical contents
- `config/` - Application configuration settings (cache, celery, db, es, logging, security, sse, token)
- `log/` - Logging configuration and utilities (logging.py, mask.py)
- `middleware.py` - Custom FastAPI middleware implementations
- `metrics.py` - Prometheus metrics collection
- `permission/` - Role-based access control (RBAC) implementation
- `security/` - Authentication, authorization, and security utilities
- `sse/` - Server-Sent Events manager for real-time notifications

## 3. How key modules work

- `config/`:
  - Input: Environment variables and .env file configurations
  - Output: Config objects for database, cache, security, etc.
  - What it does: Centralized configuration management using Pydantic Settings
  - How it interacts: Provides configuration values to all layers

- `security/`:
  - Input: JWT tokens, user credentials, HTTP requests
  - Output: Authenticated user objects, access tokens, security headers
  - What it does: Handles authentication, token management, password hashing
  - How it interacts: Used by middleware for request authentication, by API endpoints for user identification

- `log/`:
  - Input: Log messages, log levels, contextual data
  - Output: Formatted log entries in structured logging format
  - What it does: Provides centralized logging with contextual information
  - How it interacts: Imported by all services, models, and utilities

- `middleware.py`:
  - Input: HTTP requests and responses
  - Output: Modified requests/responses, logged activities
  - What it does: Processes requests before they reach handlers, implements cross-cutting concerns
  - How it interacts: Wraps all API requests, logs activities, handles CORS

- `permission/`:
  - Input: User roles, required permissions, resource context
  - Output: Permission grants/denials, role assignments
  - What it does: Implements RBAC system with role-based permissions
  - How it interacts: Used by API endpoints through dependency injection, integrates with security/

- `sse/`:
  - Input: User connections for real-time updates
  - Output: Server-Sent Events stream
  - What it does: Manages SSE connections for notifications
  - How it interacts: Used by notification service and API endpoints/

## 4. Request flow and integration
A typical HTTP request flows through the core components:
1. Request enters through FastAPI and is processed by middleware in `middleware.py`
2. HTTP logging middleware logs request details using utilities from `log/`
3. Security middleware authenticates user using components from `security/`
4. RBAC system in `permission/` validates user permissions
5. Request is passed to appropriate API handler
6. All operations are logged through the logging system from `log/`

## 5. Summary
The `app/core/` directory is the foundational layer that provides essential infrastructure services. It handles configuration management, security, logging, middleware, RBAC, and SSE. Key additions include modular `config/` directory for different configuration types and `sse/` for real-time notifications.