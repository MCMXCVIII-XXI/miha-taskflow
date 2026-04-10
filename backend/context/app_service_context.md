# app_service_context.md

## 1. Purpose of the directory
The `app/service/` directory serves as the business logic layer of the TaskFlow application. It contains service classes that implement domain-specific functionality, coordinate between data access layers (database, Elasticsearch, cache), and enforce business rules. This directory represents the "domain" or "application" architectural layer that encapsulates the core functionality of the task management system.

## 2. Typical contents
- Service implementation files for each domain entity (task.py, user.py, group.py, etc.)
- Base service classes with common functionality
- Query builder classes for complex database operations
- Utility services for specialized functionality (notifications, XP calculation, etc.)
- Utility modules for specialized operations

## 3. How key modules work
- Service classes (e.g., TaskService, UserService, GroupService):
  - Input: Domain-specific requests, user context, business parameters
  - Output: Processed domain objects, operation results, notifications
  - What it does: Implements business logic, coordinates data access, enforces rules
  - How it interacts with other layers: Uses database models from `models/`, Elasticsearch documents from `indexes/`, cache from `cache/`, schemas from `schemas/`, and raises domain-specific exceptions from `service/exceptions/` when appropriate

- Base service classes:
  - Input: Database sessions, common service dependencies
  - Output: Base functionality for all services
  - What it does: Provides common operations like cache invalidation, role management
  - How it interacts with other layers: Inherited by all service implementations, provides shared infrastructure

- Query builder classes:
  - Input: Search parameters, filtering criteria, sorting options
  - Output: SQLAlchemy query objects ready for execution
  - What it does: Builds complex database queries with proper joins and filters
  - How it interacts with other layers: Used by services to construct efficient database queries

## 4. Request flow and integration
A typical service operation flows through the service layer as follows:
1. API endpoint receives HTTP request and validates it using schemas from `schemas/`
2. API handler calls appropriate service method with validated parameters
3. Service method performs business logic:
   - Validates permissions using core/permission.py
   - Queries database using models from `models/` and query builders from `query_db/`
   - Interacts with cache from `cache/` for performance optimization
   - Indexes/searches Elasticsearch using components from `es/`
   - Raises domain-specific exceptions from `service/exceptions/` when business rule violations occur
- Service returns processed results to API handler
- API handler formats response using schemas from `schemas/` or handles exceptions and returns appropriate error responses

## 5. Summary
The `app/service/` directory is the business logic layer that implements the core functionality of the TaskFlow application. It orchestrates interactions between data access layers (database, Elasticsearch, cache) and enforces business rules. This directory is crucial for maintaining clean separation of concerns, ensuring business logic is centralized and testable, and providing a consistent interface between the API layer and data access layers.