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
    logger.info(f"bulk_index_async: model={model}, ids={ids}, batch_size={batch_size}")
    return run_async(
        outbox_task_service.bulk_index(model=model, ids=ids, batch_size=batch_size)
    )


@celery_app.task(base=ElasticsearchIndexTask, name="app.outbox_processor")  # type: ignore[untyped-decorator]
def process_outbox_async(batch_size: int = 100) -> dict[str, Any]:
    logger.info(f"process_outbox_async: batch_size={batch_size}")
    return run_async(outbox_task_service.process_outbox(batch_size=batch_size))


@celery_app.task(base=ElasticsearchIndexTask, name="app.outbox_retry_failed")  # type: ignore[untyped-decorator]
def retry_failed_outbox_async(max_retries: int = 3) -> dict[str, Any]:
    logger.info(f"retry_failed_outbox_async: max_retries={max_retries}")
    return run_async(outbox_task_service.retry_failed_outbox(max_retries=max_retries))
