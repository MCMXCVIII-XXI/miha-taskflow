# app_core_permission_context.md;

## 1. Purpose of the directory
The `app/core/permission/` directory serves as the role-based access control (RBAC) layer of the TaskFlow application. It contains permission management, role assignment, and access control utilities that enforce security policies throughout the application.

## 2. Typical contents
- `permissions.py` - Permission definitions and role-permission mappings
- `check_permission.py` - Permission checking utilities and decorators`
- `init_rbac.py` - RBAC system initialization and setup`
- `role_permissions.py` - Role and permission assignments`
- `seed_data.py` - Initial permission and role data definitions`
- `setup_role_permissions.py` - Role permission setup utilities`

## 3. How key modules work`

- `permissions.py`:
  - Input: Permission definitions, role assignments`
  - Output: Registered permissions and role mappings`
  - What it does: Defines available permissions and maps them to roles`
  - How it interacts: Used by permission checking utilities, integrated with authentication from `core/security/`

- `check_permission.py`:
  - Input: User context, required permissions, request context`
  - Output: Authorization decision (allow/deny) or permission enforcement`
  - What it does: Implements permission checking logic, provides decorators for endpoint protection`
  - How it interacts: Used by API endpoint handlers, integrates with user authentication, queries database for user roles`

- `init_rbac.py`:
  - Input: Database connection, permission configuration`
  - Output: Initialized RBAC system with roles and permissions`
  - What it does: Sets up the RBAC system at application startup`
  - How it interacts: Called during application initialization, creates database records for roles and permissions`

## 4. Request flow and integration`
A typical permission check flows through the permission layer:
1. HTTP request arrives at FastAPI and is processed by authentication middleware`
2. Authentication middleware attaches user object to request`
3. API endpoint with permission decorator is accessed`
4. `check_permission.py` evaluates user's roles and permissions`
5. RBAC system queries database for user role assignments`
6. If authorized: Request proceeds to endpoint handler`
7. If unauthorized: Request is rejected with appropriate HTTP error response`
8. All permission checks are logged through `core/log/` for audit purposes`

## 5. Summary`
The `app/core/permission/` directory is the authorization layer that implements role-based access control. It ensures users can only perform actions they are authorized to execute, protecting application resources and maintaining security. This directory integrates with the authentication system, API endpoints, and database models to provide comprehensive access control.