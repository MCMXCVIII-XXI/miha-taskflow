# app_service_exceptions_context.md

## 1. Purpose of the directory
The `app/service/exceptions/` directory serves as the domain-specific exception definition layer. It contains custom exception classes representing business logic errors for each domain entity.

## 2. Typical contents
- `task_exc.py` - Task-related exceptions (not found, access denied, conflicts)
- `user_exc.py` - User-related exceptions (not found, conflicts, validation)
- `group_exc.py` - Group-related exceptions (access denied, conflicts, membership)
- `comment_exc.py` - Comment-related exceptions
- `notifi_exc.py` - Notification-related exceptions
- `search_exc.py` - Search-related exceptions
- `rating_exc.py` - Rating-related exceptions
- `level_exc.py` - XP/level-related exceptions
- `join_request_exc.py` - Join request exceptions
- `group_membership_exc.py` - Group membership exceptions

## 3. How key modules work
- `task_exc.py`:
  - Input: Task operation error conditions and context information
  - Output: Properly formatted exception objects with HTTP status codes
  - What it does: Defines specific exceptions for task management operations
  - How it interacts with other layers: Used by TaskService in `service/task.py` to handle task-specific errors, caught by FastAPI exception handlers in `main.py` and converted to HTTP responses

- `user_exc.py`:
  - Input: User operation error conditions (authentication, profile issues)
  - Output: Exception objects representing user-related errors
  - What it does: Provides specific exceptions for user management and authentication failures
  - How it interacts with other layers: Used by UserService in `service/user.py` and authentication components in `core/security/`, handled by API exception handlers

- `group_exc.py`:
  - Input: Group operation error conditions (membership, access control)
  - Output: Exception objects representing group-related errors
  - What it does: Defines exceptions for group management and membership operations
  - How it interacts with other layers: Used by GroupService in `service/group.py`, integrated with RBAC system in `core/permission/`

## 4. Request flow and integration
A typical exception flow through the service exceptions layer:
1. Service method in `service/` encounters an error condition during business logic execution
2. Service raises appropriate domain-specific exception from this directory
3. Exception propagates up through service call stack
4. FastAPI exception handlers in `main.py` catch specific exception types
5. Exception handlers convert exceptions to proper HTTP error responses with status codes
6. Error response is formatted using standardized error schemas
7. Client receives meaningful error information with appropriate HTTP status code
8. All exceptions are logged through `core/log/` for monitoring and debugging

## 5. Summary
The `app/service/exceptions/` directory is the domain-specific error modeling layer that provides meaningful error information for different business logic failure scenarios. It ensures consistent error handling across the application by defining specific exceptions for each domain entity. This directory integrates with service implementations to handle business logic errors and with the API layer to provide proper HTTP error responses. It serves as a critical component for maintaining a good user experience by providing clear, actionable error information.