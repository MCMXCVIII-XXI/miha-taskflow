from typing import ClassVar

from celery import Task
from elasticsearch.exceptions import ConnectionError as ESConnectionError


class ElasticsearchIndexTask(Task):  # type: ignore[misc]
    """
    Base Celery task class for Elasticsearch indexing operations.

    Provides automatic retry logic for transient failures.
    Used by: bulk_index_async, process_outbox_async, retry_failed_outbox_async.

    RETRY POLICY:
    ├── Triggers: ES connection errors, timeouts
    ├── Backoff: Exponential (1s → 2s → 4s → ... → max 5min)
    ├── Max retries: 3 attempts per task
    └── After 3 fails → Dead Letter Queue (retry_failed_outbox_async)

    Example:
        @celery_app.task(base=ElasticsearchIndexTask)
        def bulk_index_async(): ...
    """

    # Auto-retry on ES/network failures
    autoretry_for = (
        ESConnectionError,  # ES cluster unavailable
        TimeoutError,  # Connection/request timeout (from your imports)
    )

    # Exponential backoff
    retry_backoff = True

    # Max delay: 5 minutes
    retry_backoff_max = 300

    retry_kwargs: ClassVar[dict[str, int]] = {"max_retries": 3}
