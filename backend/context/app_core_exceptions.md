# app_core_exceptions.md

## 1. Purpose of the directory
The `app/core/exceptions/` directory contains base exception classes for infrastructure layers such as RBAC (access control) and security.

## 2. Typical contents
- `rbac_exc.py` - Role-Based Access Control (RBAC) system exceptions.
- `security_exc.py` - Security exceptions.

## 3. How key modules work
- `BaseRBACError` (in `rbac_exc.py`):
  - Input: HTTP code, message, headers.
  - Output: Exception object.
  - What it does: Base class for all access control errors (roles not found, already exist, etc.).
  - How it interacts: Handled in `main.py` via `@app.exception_handler`.

- `BaseSecurityError` (in `security_exc.py`):
  - Input: Authentication error data.
  - Output: Exception object.
  - What it does: Base class for security errors (invalid token, wrong password).
  - How it interacts: Used in `app/core/security/`.

## 4. Data flow and integration
1. A service or middleware detects a security or access control violation.
2. A specific exception is raised (e.g., `RoleNotFound`).
3. FastAPI catches it via the registered handler.
4. A JSON response with the appropriate status (404, 403, etc.) is returned.

## 5. Summary
Provides a standardized way to handle critical infrastructure errors, separating error handling logic from service business logic.
