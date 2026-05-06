# app_service_transactions.md

## 1. Purpose of the directory
The `app/service/transactions/` directory contains transaction classes that ensure atomicity of operations affecting multiple repositories or business logic steps. Implements the Unit of Work (UoW) pattern.

## 2. Typical contents
- `__init__.py` - Exports all transactions and dependency factories.
- `base.py` - `BaseTransaction`: Base class with UoW creation logic.
- `task.py` - `TaskTransaction`: Transactions for task creation and updates.
- `user.py` - `UserTransaction`: Transactions for users.
- `group.py` - `GroupTransaction`: Transactions for groups.
- `auth.py` - `AuthTransaction`: Authentication transactions.
- `comment.py`, `rating.py`, `notification.py`, `xp.py`, `admin.py` - Specific transactions.

## 3. How key modules work
- `BaseTransaction`:
  - Input: UnitOfWork class, session factory.
  - Output: Transaction instance.
  - What it does: Provides `_create_uow()` method for creating isolated DB context.
  - How it interacts: Inherited by all transactions.

- `TaskTransaction` (example):
  - Input: Task parameters, user.
  - Output: Operation result.
  - What it does: Combines calls to `TaskRepository`, `GroupRepository`, `NotificationService` into one atomic DB transaction.
  - How it interacts: Uses `UnitOfWork` from `app/repositories/uow.py`.

## 4. Data flow and integration
1. A service (e.g., `TaskService`) calls a transaction method.
2. The transaction creates a `UnitOfWork`.
3. Inside UoW, operations with multiple repositories are executed.
4. If all successful — `uow.commit()`, otherwise — `uow.rollback()`.

## 5. Summary
Transaction layer guarantees data consistency in complex TaskFlow business operations where changing one entity entails changing related ones (e.g., task creation + notification + role updates).
