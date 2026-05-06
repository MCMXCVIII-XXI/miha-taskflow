# app_background_exceptions.md

## 1. Purpose of the directory
The `app/background/exceptions/` directory contains exceptions specific to background tasks (Celery), such as broker connection errors or task execution timeouts.

## 2. Typical contents
- `__init__.py` - Package initialization.
- `bt_exc.py` - Background task exceptions (Background Task Exceptions).

## 3. How key modules work
- `BaseBackgroundError`:
  - Input: Message, HTTP code (default 500).
  - Output: Exception object.
  - What it does: Base class for all worker errors.
  - How it interacts: Used in Celery tasks to raise errors.

- `BackgroundBrokerUrlError`: Broker URL error (Redis/RabbitMQ).
- `BackgroundBackendUrlError`: Backend result error.
- `BackgroundAsyncTimeoutError`: Async task wait timeout exceeded.
- `BackgroundRuntimeError`: Task execution error.

## 4. Data flow and integration
1. A Celery task encounters an error (e.g., no Redis connection).
2. An exception is raised from this module.
3. The error is logged or sent to Sentry.

## 5. Summary
An isolated error layer for asynchronous tasks, helping to separate broker infrastructure failures from business logic errors.
