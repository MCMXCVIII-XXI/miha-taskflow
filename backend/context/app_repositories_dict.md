# app_repositories_dict.md

## 1. Purpose of the directory
The `app/repositories/dict/` directory contains typed dictionaries (TypedDict) and helper classes used by repositories to build complex queries, such as fuzzy search (ilike).

## 2. Typical contents
- `__init__.py` - Package initialization.
- `user.py` - Data types for user search.

## 3. How key modules work
- `UserIlike` (in `user.py`):
  - Input: String fields (username, email, first_name, etc.).
  - Output: Dictionary with parameters for SQL query with `ILIKE`.
  - What it does: Defines structure for passing search patterns to `UserRepository`.
  - How it interacts: Used in `find_many` or `get` methods of the user repository.

## 4. Data flow and integration
1. A service forms search parameters (e.g., `{"username": "%admin%"}`).
2. Data is passed to the repository according to the `UserIlike` type.
3. The repository converts them to SQL expressions `where(column.ilike(pattern))`.

## 5. Summary
A reference of data types for the data access layer, simplifying filter and search query construction while maintaining strict typing.
