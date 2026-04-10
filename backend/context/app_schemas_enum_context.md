# app_schemas_enum_context.md

## 1. Purpose of the directory
The `app/schemas/enum/` directory serves as the standardized value definition layer of the TaskFlow application. It contains enumerations that define valid values for various domain concepts, ensuring data consistency and type safety across the application. This directory represents the domain constants layer that provides a single source of truth for allowed values and state representations.

## 2. Typical contents
- `task.py` - Task-related enumerations (status, priority, difficulty, visibility)
- `group.py` - Group-related enumerations (visibility, join policy)
- `role.py` - Role and permission enumerations
- `notification.py` - Notification type and status enumerations
- `level.py` - User level and XP-related enumerations
- `rating.py` - Rating and feedback enumerations
- `token.py` - Token type and status enumerations
- `__init__.py` - Enum module initialization and exports

## 3. How key modules work
- `task.py`:
  - Input: Task state and attribute definitions
  - Output: Standardized task enumeration values
  - What it does: Defines valid values for task properties like status, priority, and difficulty
  - How it interacts with other layers: Used by task models in `models/`, task schemas in `schemas/`, and task services in `service/` to ensure consistent value usage

- `group.py`:
  - Input: Group property definitions and policies
  - Output: Standardized group enumeration values
  - What it does: Defines valid values for group visibility and membership policies
  - How it interacts with other layers: Used by group models in `models/`, group schemas in `schemas/`, and group services in `service/` to maintain consistency in group management

- `role.py`:
  - Input: Role and permission definitions
  - Output: Standardized role enumeration values
  - What it does: Defines user roles and permission levels within the application
  - How it interacts with other layers: Used by RBAC system in `core/permission/`, user models in `models/`, and authentication components in `core/security/` to manage access control

## 4. Request flow and integration
A typical enum usage flow through the schemas/enum layer:
1. API endpoint in `api/v1/endpoints/` receives request with enum values
2. FastAPI validates enum values against definitions in this directory using schemas from `schemas/`
3. Service in `service/` processes request using enum values from this directory
4. Database operations through models in `models/` use enum values for storage
5. Elasticsearch indexing in `es/indexer.py` stores enum values for search
6. Response schemas in `schemas/` format enum values for client consumption
7. All enum values are consistent across the entire application stack

## 5. Summary
The `app/schemas/enum/` directory is the standardized value definition layer that provides consistent, type-safe enumerations for the TaskFlow application. It ensures data integrity by defining allowed values for domain concepts and preventing invalid states. This directory integrates with all other layers by providing shared constants that maintain consistency across models, schemas, services, and API endpoints. It serves as a critical data validation component that prevents errors and ensures predictable behavior throughout the application.