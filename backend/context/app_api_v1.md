# app_api_v1.md

## 1. Purpose of the directory
The `app/api/v1/` directory serves as the main router assembly point for all version 1 API endpoints in TaskFlow. It aggregates routes from various domain areas.

## 2. Typical contents
- `__init__.py` - Creates `api_router` and includes routers from the `endpoints/` subdirectory.
- `endpoints/` - Subdirectory containing specific endpoint files.
  - `main.py` - Health check and Prometheus metrics endpoints

## 3. How the key module works
- `api_router` (in `__init__.py`):
  - Input: Routers from `endpoints/` (admin_router, auth_router, tasks_router, etc.).
  - Output: Single `APIRouter` object.
  - What it does: Aggregates all routes, sets prefixes (e.g., `/admin`, `/auth`) and tags for Swagger documentation.
  - How it interacts: Imported in `main.py` and included in the main FastAPI application.

## 4. Data flow and integration
1. Each file in `endpoints/` defines its own router.
2. In `__init__.py`, these routers are imported and included in `api_router` with path prefixes.
3. `api_router` is included in `app` in `main.py`.

## 5. Summary
The main routing node for version 1, ensuring modularity and a clear API structure for TaskFlow.
