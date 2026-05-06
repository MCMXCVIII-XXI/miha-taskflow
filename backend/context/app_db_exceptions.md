# app_db_exceptions.md

## 1. Purpose of the directory
The `app/db/exceptions/` directory contains database-specific exceptions, allowing services to catch DB errors as domain errors.

## 2. Typical contents
- `db_exc.py` - Base and derived database exceptions.

## 3. How key modules work
- `BaseDBError`:
  - Input: Error message, HTTP code.
  - Output: Exception object.
  - What it does: Base class for database errors.
  - How it interacts: Can be used in `app/db/` helpers.

- `DBConnectionError`:
  - Input: Connection failure message.
  - Output: Exception with 500 status.
  - What it does: Signals inability to connect to the database.

- `DBRuntimeError`:
  - Input: Query execution error.
  - Output: Exception with 500 status.
  - What it does: Signals SQLAlchemy runtime errors.

## 4. Data flow and integration
1. The data access layer (repositories or db_helper) encounters an error.
2. The error is wrapped in `BaseDBError` or its descendants.
3. The exception is propagated to the service layer or caught globally.

## 5. Summary
Isolated database exception layer, allowing abstraction from specific driver errors (e.g., asyncpg or psycopg) and providing a unified error interface.
