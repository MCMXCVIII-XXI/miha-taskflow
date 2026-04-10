# app_core_permission_context.md

## 1. Purpose of the directory
The `app/core/permission/` directory serves as the role-based access control (RBAC) layer of the TaskFlow application. It contains permission management, role assignment, and access control utilities that enforce security policies throughout the application. This directory represents the authorization infrastructure layer that ensures users can only perform actions they are permitted to execute.

## 2. Typical contents
- `permissions.py` - Permission definitions and role-permission mappings
- `check_permission.py` - Permission checking utilities and decorators
- `init_rbac.py` - RBAC system initialization and setup
- `setup_role_permissions.py` - Role and permission seeding utilities
- `seed_data.py` - Initial permission and role data definitions
- `__init__.py` - Permission module initialization and exports

## 3. How key modules work
- `permissions.py`:
  - Input: Permission definitions, role-permission mappings
  - Output: Registered permissions and role assignments
  - What it does: Defines available permissions and maps them to roles
  - How it interacts with other layers: Used by permission checking utilities in `check_permission.py`, integrated with authentication from `core/security/`, referenced by endpoint decorators in `api/v1/endpoints/`

- `check_permission.py`:
  - Input: User context, required permissions, request context
  - Output: Authorization decision (allow/deny) or permission enforcement
  - What it does: Implements permission checking logic, provides decorators for endpoint protection
  - How it interacts with other layers: Used by API endpoint handlers in `api/v1/endpoints/` to enforce access control, integrates with user authentication from `core/security/`, queries database models from `models/` for user roles

- `init_rbac.py`:
  - Input: Database connection, permission configuration
  - Output: Initialized RBAC system with roles and permissions
  - What it does: Sets up the RBAC system at application startup
  - How it interacts with other layers: Called during application initialization in `main.py`, creates database records in `models/` for roles and permissions, integrates with configuration from `core/config.py`

## 4. Request flow and integration
A typical permission check flows through the permission layer as follows:
1. HTTP request arrives at an API endpoint protected by a permission decorator
2. Authentication middleware from `core/security/` authenticates user and attaches user object to request
3. Permission decorator from `check_permission.py` extracts required permission from endpoint definition
4. Permission checker queries database through `models/` to retrieve user roles and permissions
5. RBAC system evaluates whether user has required permission based on role assignments
6. If authorized: Request proceeds to endpoint handler
7. If unauthorized: Request is rejected with appropriate HTTP error response
8. All permission checks are logged through `core/log/` for audit purposes

## 5. Summary
The `app/core/permission/` directory is the authorization layer that implements role-based access control for the TaskFlow application. It ensures users can only perform actions they are authorized to execute, protecting application resources and maintaining security. This directory integrates with the authentication system, API endpoints, and database models to provide comprehensive access control. It serves as a critical security infrastructure component that enforces the principle of least privilege throughout the application.