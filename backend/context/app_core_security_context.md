# app_core_security_context.md

## 1. Purpose of the directory
The `app/core/security/` directory serves as the authentication and security infrastructure layer of the TaskFlow application. It contains components for user authentication, password management, token handling, and security utilities that protect the application from unauthorized access. This directory represents the identity and access management layer that ensures only legitimate users can access the system.

## 2. Typical contents
- `auth.py` - Authentication utilities and user validation
- `hash.py` - Password hashing and verification utilities
- `token.py` - JWT token creation, validation, and management
- `__init__.py` - Security module initialization and exports
- Security configuration and validation utilities
- Password strength checking and policy enforcement

## 3. How key modules work
- `auth.py`:
  - Input: User credentials, authentication requests, security context
  - Output: Authenticated user objects, authentication decisions
  - What it does: Verifies user credentials, manages authentication state, integrates with database models
  - How it interacts with other layers: Used by API endpoint handlers in `api/v1/endpoints/auth.py` for login operations, integrates with user models from `models/`, works with password hashing from `hash.py`, provides user context to permission system in `core/permission/`

- `hash.py`:
  - Input: Plain text passwords, password hashes for verification
  - Output: Hashed passwords, verification results
  - What it does: Provides secure password hashing and verification using industry-standard algorithms
  - How it interacts with other layers: Used by authentication components in `auth.py`, interacts with user models from `models/` during password validation, called by services in `service/` when handling password updates

- `token.py`:
  - Input: User identity, token claims, expiration parameters
  - Output: JWT tokens, token validation results, user identity from tokens
  - What it does: Creates, signs, and validates JWT tokens for session management
  - How it interacts with other layers: Used by authentication in `auth.py` to create session tokens, consumed by middleware components to authenticate requests, integrates with configuration from `core/config.py` for token settings

## 4. Request flow and integration
A typical authentication flow through the security layer:
1. User submits login credentials to auth endpoint in `api/v1/endpoints/auth.py`
2. Endpoint calls authentication utilities in `auth.py` with provided credentials
3. Authentication component hashes provided password using `hash.py` and compares with stored hash from database models in `models/`
4. If credentials are valid, token generator in `token.py` creates JWT token with user claims
5. Token is returned to client in HTTP response
6. Subsequent requests include token in Authorization header
7. Middleware extracts token and validates using `token.py`
8. Validated user identity is attached to request context for use by permission system in `core/permission/`
9. All security operations are logged through `core/log/` for audit purposes

## 5. Summary
The `app/core/security/` directory is the authentication and identity management layer that protects the TaskFlow application from unauthorized access. It provides secure password handling, token-based session management, and user authentication services. This directory integrates with the API layer for login endpoints, the permission system for access control, and the database models for user data validation. It serves as a critical security infrastructure component that establishes the trust boundary for all application interactions.