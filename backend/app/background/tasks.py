from typing import Any, Literal

from app.core.log import logging
from app.service import outbox_task_service

from .base import ElasticsearchIndexTask
from .celery import celery_app
from .runner import run_async

logger = logging.get_logger(__name__)


@celery_app.task(base=ElasticsearchIndexTask, name="app.bulk_index")  # type: ignore[untyped-decorator]
def bulk_index_async(
    model: Literal["task", "user", "group", "comment"],
    ids: list[int] | None = None,
    batch_size: int = 100,
) -> dict[str, Any]:
    """
    Celery task: Bulk indexes entities (tasks/users/groups/comments) into Elasticsearch.

    Converts model IDs to ES documents and indexes them in batches.
    Uses async outbox pattern for reliability.

    Args:
        model: Entity type to index ("task", "user", "group", "comment")
        ids: Specific IDs to index (None = all pending from outbox)
        batch_size: Number of documents per ES bulk request (default: 100)

    Returns:
        dict with indexing stats: {"success": N, "failed": M, "total": N+M}

    Example:
        bulk_index_async("task", [1, 2, 3], batch_size=50)
    """
    logger.info(f"bulk_index_async: model={model}, ids={ids}, batch_size={batch_size}")
    return run_async(
        outbox_task_service.bulk_index(model=model, ids=ids, batch_size=batch_size)
    )


@celery_app.task(base=ElasticsearchIndexTask, name="app.outbox_processor")  # type: ignore[untyped-decorator]
def process_outbox_async(batch_size: int = 100) -> dict[str, Any]:
    """
    Celery task: Processes transactional outbox for pending index operations.

    Scans outbox table for unprocessed indexing events (CREATE/UPDATE/DELETE).
    Converts events to ES bulk operations and marks as processed.

    Args:
        batch_size: Max outbox records to process per run (default: 100)

    Returns:
        dict with processing stats: {"processed": N, "failed": M}

    Example:
        process_outbox_async(batch_size=200)  # Scale for load
    """
    logger.info(f"process_outbox_async: batch_size={batch_size}")
    return run_async(outbox_task_service.process_outbox(batch_size=batch_size))


@celery_app.task(base=ElasticsearchIndexTask, name="app.outbox_retry_failed")  # type: ignore[untyped-decorator]
def retry_failed_outbox_async(max_retries: int = 3) -> dict[str, Any]:
    """
    Celery task: Retries previously failed outbox indexing operations.

    Finds outbox records with failed attempts < max_retries.
    Reattempts indexing with exponential backoff.

    Args:
        max_retries: Maximum retry attempts per outbox record (default: 3)

    Returns:
        dict with retry stats: {"retried": N, "gave_up": M, "success": K}

    Example:
        retry_failed_outbox_async(max_retries=5)  # Aggressive recovery
    """
    logger.info(f"retry_failed_outbox_async: max_retries={max_retries}")
    return run_async(outbox_task_service.retry_failed_outbox(max_retries=max_retries))
