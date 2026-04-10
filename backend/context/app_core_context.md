# app_core_context.md

## 1. Purpose of the directory
The `app/core/` directory serves as the foundational infrastructure layer of the TaskFlow application. It contains core application configurations, security implementations, logging utilities, middleware components, and shared utilities that are used across all other layers. This directory represents the "core" architectural layer that provides essential services to the entire application.

## 2. Typical contents
- `config.py` - Application configuration settings using Pydantic Settings
- `security/` - Authentication, authorization, and security-related utilities
- `log.py` - Logging configuration and utility functions
- `middleware/` - Custom FastAPI middleware implementations
- `exceptions/` - Custom exception definitions organized by domain
- `sse/` - Server-Sent Events implementation for real-time notifications
- `permission.py` - Role-based access control (RBAC) implementation

## 3. How key modules work
- `config.py`:
  - Input: Environment variables and .env file configurations
  - Output: Config objects for database, cache, security, etc.
  - What it does: Centralized configuration management using Pydantic Settings
  - How it interacts with other layers: Provides configuration values to database helpers, cache implementations, security components, and Elasticsearch clients

- `security/`:
  - Input: JWT tokens, user credentials, HTTP requests
  - Output: Authenticated user objects, access tokens, security headers
  - What it does: Handles authentication, token management, password hashing
  - How it interacts with other layers: Used by middleware for request authentication, by permission system for access control, and by API endpoints for user identification

- `log.py`:
  - Input: Log messages, log levels, contextual data
  - Output: Formatted log entries in structured logging format
  - What it does: Provides centralized logging with contextual information
  - How it interacts with other layers: Imported by all services, models, and utilities to log operations, errors, and debug information

- `middleware/`:
  - Input: HTTP requests and responses
  - Output: Modified requests/responses, logged activities
  - What it does: Processes requests before they reach handlers, implements cross-cutting concerns
  - How it interacts with other layers: Wraps all API requests, logs activities, handles CORS, and manages security headers

- `exceptions/`:
  - Input: Error conditions, domain-specific validation failures
  - Output: Properly formatted HTTP error responses
  - What it does: Defines custom exception classes for different error scenarios
  - How it interacts with other layers: Used throughout services and API handlers to handle business logic errors

## 4. Request flow and integration
A typical HTTP request flows through the core components as follows:
1. Request enters through FastAPI and is processed by middleware in `middleware/`
2. HTTP logging middleware logs request details using utilities from `log.py`
3. Security middleware authenticates user using components from `security/`
4. RBAC system in `permission.py` validates user permissions
5. Request is passed to appropriate API handler
6. Handler may raise custom exceptions from `exceptions/` which are formatted into proper HTTP responses
7. All operations are logged using the logging system from `log.py`

## 5. Summary
The `app/core/` directory is the foundational layer that provides essential infrastructure services to the entire application. It handles configuration management, security, logging, middleware, and exception handling. This layer is crucial for maintaining consistency across the application and implementing cross-cutting concerns like authentication, authorization, and request logging. It integrates with all other layers by providing shared utilities and handling common concerns like security and error management.