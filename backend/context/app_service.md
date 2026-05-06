# app_service_context.md

## 1. Purpose of the directory
The `app/service/` directory serves as the business logic layer of the TaskFlow application. It contains service classes that implement domain-specific functionality, coordinate between data access layers (database, Elasticsearch, cache), and enforce business rules. This directory represents the "domain" or "application" architectural layer that encapsulates the core functionality.

## 2. Typical contents
- Service implementation files for each domain entity (task.py, user.py, group.py, etc.)
- Base service classes with common functionality
- Transaction services for atomic operations (transactions/)
- Search services (search/)
- Service utilities (utils/)
- Service exceptions (exceptions/)
- Bulk operations (bulk.py)
- Outbox pattern (outbox.py)
- SSE service (sse.py)

### Main Services
- `task.py` - Task management and assignments
- `user.py` - User profile and authentication
- `group.py` - Group management
- `auth.py` - Authentication service
- `notification.py` - Notifications
- `xp.py` - XP and leveling
- `rating.py` - Ratings
- `comment.py` - Comments
- `admin.py` - Admin operations
- `base.py` - Base service with common functionality
- `bulk.py` - Bulk operations
- `outbox.py` - Outbox pattern for event processing
- `sse.py` - Server-Sent Events service

### Subdirectories
- `transactions/` - Transaction services for atomic DB operations
- `search/` - Search services (DB and ES)
- `utils/` - Service utilities
- `exceptions/` - Domain-specific exceptions

## 3. How key modules work
- Service classes (e.g., TaskService, UserService, GroupService):
  - Input: Domain-specific requests, user context, business parameters
  - Output: Processed domain objects, operation results, notifications
  - What it does: Implements business logic, coordinates data access, enforces rules
  - How it interacts with other layers: Uses models from `models/`, repositories from `repositories/`, cache from `cache/`, schemas from `schemas/`, and raises exceptions from `service/exceptions/`

- Transaction services (transactions/):
  - Input: Business operations requiring atomicity
  - Output: Processed results with committed transactions
  - What it does: Provides transactional consistency across multiple operations
  - How it interacts with other layers: Uses UnitOfWork from `repositories/uow.py`, coordinates with notification service

- Bulk operations (bulk.py):
  - Input: Batch operations on multiple entities
  - Output: Processed batch results
  - What it does: Handles bulk create/update/delete operations efficiently

- Outbox pattern (outbox.py):
  - Input: Business events that need to be processed asynchronously
  - Output: Event processing and propagation
  - What it does: Implements outbox pattern for reliable event publishing

- SSE service (sse.py):
  - Input: Client connections for real-time updates
  - Output: Streaming events to connected clients
  - What it does: Manages Server-Sent Events connections for notifications

## 4. Request flow and integration
A typical service operation flows through the service layer:
1. API endpoint validates request using schemas from `schemas/`
2. API handler calls appropriate service method with validated parameters
3. Service method performs business logic:
   - Validates permissions using `core/permission/`
   - Queries database using repositories from `repositories/`
   - Interacts with cache from `cache/` for performance
   - Indexes/searches Elasticsearch using components from `es/`
   - Uses transactions for atomic operations
   - Raises domain-specific exceptions from `service/exceptions/`
4. Service returns processed results to API handler
5. API handler formats response or handles exceptions

## 5. Summary
The `app/service/` directory is the business logic layer implementing core functionality. It orchestrates interactions between data access layers and enforces business rules. Key additions include transaction services for atomic operations, bulk operations for efficient batch processing, outbox pattern for reliable async events, and SSE service for real-time notifications.
