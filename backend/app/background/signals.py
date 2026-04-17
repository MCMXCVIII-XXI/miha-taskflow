from typing import Any

from celery import Task
from celery.signals import task_failure, task_success

from app.core.log import logging

logger = logging.get_logger(__name__)


@task_failure.connect  # type: ignore[untyped-decorator]
def on_task_failure(
    sender: Task | None = None,
    request: Any | None = None,
    exception: BaseException | None = None,
    **kwargs: Any,
) -> None:
    """
    Celery signal handler: Logs task failures with structured metadata.

    Automatically triggered when ANY Celery task raises an exception.
    Provides full traceback + task context for debugging.

    Triggered for:
    - ES indexing failures
    - DB timeouts
    - Network errors
    - Business logic exceptions

    Args:
        sender: Task instance (or None)
        request: Task request object with id/name/retries
        exception: Caught exception instance
        kwargs: Additional Celery context

    Logged fields:
        - task_id: Unique task UUID
        - task_name: "app.bulk_index", "app.outbox_processor", etc.
        - retries: Current retry count (0-N)
        - exception: Exception message
        - traceback: Full stack trace (exc_info=True)
    """
    if request is None:
        logger.error("Celery task failed (request is None)", exc_info=True)
        return

    task_id = getattr(request, "id", None)
    task_name = getattr(request, "name", None)
    retries = getattr(request, "retries", 0)

    extra = {
        "task_id": task_id,
        "task_name": task_name,
        "exception": str(exception) if exception else None,
        "retries": retries,
    }

    logger.error(
        "Celery task failed",
        extra=extra,
        exc_info=True,  # Full traceback in logs
    )


@task_success.connect  # type: ignore[untyped-decorator]
def on_task_success(
    sender: Task | None = None,
    request: Any | None = None,
    **kwargs: Any,
) -> None:
    """
    Celery signal handler: Logs successful task completion.

    Tracks successful ES indexing, outbox processing, retries.
    Helps monitor task throughput and reliability.

    Args:
        sender: Task instance (or None)
        request: Task request with id/name/retries
        kwargs: Additional Celery context

    Logged fields:
        - task_id: Task UUID
        - task_name: Task name (bulk_index, outbox_processor, etc.)
        - retries: Number of retry attempts (usually 0)
    """
    if request is None:
        logger.info("Celery task succeeded (no request info)")
        return

    task_id = getattr(request, "id", None)
    task_name = getattr(request, "name", None)
    retries = getattr(request, "retries", 0)

    logger.info(
        "Celery task succeeded",
        extra={
            "task_id": task_id,
            "task_name": task_name,
            "retries": retries,
        },
    )
