# app_repositories_context.md

## 1. Purpose of the directory
The `app/repositories/` directory serves as the data access layer (DAO) of the TaskFlow application. It contains repository classes that handle all database operations for each domain entity. This directory represents the persistence layer that abstracts SQLAlchemy queries and provides a clean interface for service implementations.

## 2. Typical contents
- `task.py` - TaskRepository for task CRUD and queries
- `user.py` - UserRepository for user operations
- `group.py` - GroupRepository for group operations
- `comment.py` - CommentRepository for comments
- `notification.py` - NotificationRepository for notifications
- `rating.py` - RatingRepository for ratings
- `join.py` - JoinRequestRepository for join requests
- `outbox.py` - OutboxRepository for outbox events
- `role.py` - RoleRepository for RBAC roles
- `task_assignee.py` - TaskAssigneeRepository for task assignments
- `group_membership.py` - GroupMembershipRepository for group members
- `user_role.py` - UserRoleRepository for user roles
- `user_skill.py` - UserSkillRepository for XP skills
- `uow.py` - UnitOfWork for transaction management
- `dict/user.py` - Dictionary repository for user's dictionary data

## 3. How key modules work
- `TaskRepository`:
  - Input: Task filters, pagination, sorting options
  - Output: Task SQLAlchemy models or lists
  - What it does: Handles all task database operations (CRUD, search, filtering)
  - How it interacts with other layers: Used by TaskService in `service/task.py`, works with TaskModel from `models/`

- `UserRepository`:
  - Input: User filters, search parameters
  - Output: User SQLAlchemy models
  - What it does: Manages user data persistence
  - How it interacts with other layers: Used by UserService and AuthService, integrates with UserModel

- `GroupRepository`:
  - Input: Group filters, membership queries
  - Output: Group SQLAlchemy models
  - What it does: Handles group operations and member management
  - How it interacts with other layers: Used by GroupService

- `UnitOfWork` (uow.py):
  - Input: Database session
  - Output: Aggregated repository access with transaction support
  - What it does: Provides atomic transactions across multiple repositories
  - How it interacts with other layers: Used by transactions in `service/transactions/`

## 4. Request flow and integration
A typical database operation flow through the repositories layer:
1. Service receives a request that requires database operations
2. Service creates or uses existing database session from `db/`
3. Service calls appropriate repository method
4. Repository executes SQLAlchemy query with proper filters and joins
5. Query results are returned to service
6. Service processes results for business logic

## 5. Summary
The `app/repositories/` directory is the data access layer that provides clean abstraction over SQLAlchemy operations. It encapsulates all database queries and provides transaction support through UnitOfWork. This directory integrates with service implementations to ensure proper data persistence andQuery operations while maintaining separation of concerns between business logic and data access.