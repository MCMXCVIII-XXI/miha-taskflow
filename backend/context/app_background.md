# app_background_context.md;

## 1. Purpose of the directory`
The `app/background/` directory serves as the asynchronous task processing layer of the TaskFlow application. It contains Celery task definitions, beat schedule, signals, and runner configurations. This directory handles all background processing, periodic tasks, and async operations.

## 2. Typical contents`
- `__init__.py` - Background module initialization and exports`
- `celery.py` - Celery application configuration and task definitions`
- `beat.py` - Celery beat schedule for periodic tasks`
- `base.py` - Base task classes and common functionality`
- `runner.py` - Task runner and execution utilities`
- `signals.py` - Celery signal handlers and hooks`
- `tasks.py` - Task definitions for async operations`

## 3. How key modules work`

- `celery.py`:
  - Input: Celery configuration, broker URL, result backend`
  - Output: Configured Celery application instance`
  - What it does: Initializes Celery app, configures broker/backend, registers tasks`
  - How it interacts with other layers: Used by services in `service/` for async operations, integrates with Redis for broker`

- `beat.py`:
  - Input: Schedule definitions, periodic task intervals`
  - Output: Configured beat schedule`
  - What it does: Defines periodic tasks (e.g., cleanup, reminders)`
  - How it interacts with other layers: Triggers tasks in `tasks.py`, uses services for business logic`

- `tasks.py`:
  - Input: Task parameters, business data`
  - Output: Task execution results, updated data`
  - What it does: Implements async operations (ES indexing, notifications, outbox processing)`
  - How it interacts with other layers: Uses services from `service/`, repositories from `repositories/`, ES from `es/``

## 4. Request flow and integration`
A typical background task flow:
1. Service triggers async operation (e.g., ES indexing)`
2. Service calls Celery task via `celery.py``
3. Task is queued in Redis broker`
4. Celery worker picks up task from queue`
5. Task executes using services and repositories`
6. Task updates database, Elasticsearch, or sends notifications`
7. Task result is stored (if needed)`

## 5. Summary`
The `app/background/` directory is the asynchronous processing layer that handles background tasks through Celery. It enables non-blocking operations, periodic tasks, and reliable async processing. Key components include Celery app configuration, beat scheduler, and task definitions.