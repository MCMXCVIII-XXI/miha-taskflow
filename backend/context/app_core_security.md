# app_core_security_context.md;

## 1. Purpose of the directory
The `app/core/security/` directory serves as the authentication and security infrastructure layer of the TaskFlow application. It contains components for user authentication, password management, token handling, and security utilities that protect the application from unauthorized access.

## 2. Typical contents
- `auth.py` - Authentication utilities and user validation
- `hash.py` - Password hashing and verification utilities`
- `token.py` - JWT token creation, validation, and management`

## 3. How key modules work`

- `auth.py`:
  - Input: User credentials, authentication requests`
  - Output: Authenticated user objects, authentication decisions`
  - What it does: Verifies user credentials, manages authentication state`
  - How it interacts: Used by middleware for request authentication, by API endpoints for user identification, integrates with user models from `models/`

- `hash.py`:
  - Input: Plain text passwords, password hashes for verification`
  - Output: Hashed passwords, verification results`
  - What it does: Provides secure password hashing and verification using industry-standard algorithms`
  - How it interacts: Used by authentication components in `auth.py`, interacts with user models from `models/`, called by services when handling password updates`

- `token.py`:
  - Input: User identity, token claims, expiration parameters`
  - Output: JWT tokens, token validation results, user identity from tokens`
  - What it does: Creates, signs, and validates JWT tokens for session management`
  - How it interacts: Used by authentication in `auth.py` to create session tokens, consumed by middleware components to authenticate requests, integrates with configuration from `core/config/` for token settings`

## 4. Request flow and integration`
A typical authentication flow through the security layer:
1. User submits login credentials to auth endpoint`
2. API handler calls authentication utilities in `auth.py` with provided credentials`
3. Authentication component verifies password using `hash.py``
4. If credentials are valid, token generator in `token.py` creates JWT token with user claims`
5. Token is returned to client in HTTP response`
6. Subsequent requests include token in Authorization header`
7. Middleware extracts and validates token using `token.py``
8. Validated user identity is attached to request for use by permission system`

## 5. Summary`
The `app/core/security/` directory is the authentication and identity management layer that protects the TaskFlow application from unauthorized access. It provides secure password handling, token-based session management, and user authentication services. This directory integrates with the API layer for login endpoints, the permission system for access control, and the database models for user data validation.