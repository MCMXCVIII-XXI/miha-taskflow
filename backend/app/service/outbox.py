from datetime import UTC, datetime
from typing import Any, Literal

from elasticsearch import AsyncElasticsearch
from elasticsearch.dsl import AsyncDocument
from fastapi import Depends
from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.background.exceptions import bt_exc
from app.core.log import logging
from app.core.metrics import METRICS
from app.db import Base, db_helper
from app.documents import CommentDoc, TaskDoc, UserDoc, UserGroupDoc
from app.es.client import es_helper
from app.es.indexer import ElasticsearchIndexer
from app.models import (
    Comment,
    Task,
    User,
    UserGroup,
)
from app.models.outbox import Outbox
from app.schemas.enum import OutboxEventType, OutboxStatus

from .base import BaseService

logger = logging.get_logger(__name__)


class OutboxService(BaseService):
    """Outbox service for managing outbox events.

    This service provides functionality for managing outbox events, including
    retrieving, processing, and marking as completed or failed.

    Args:
        db (AsyncSession): Database session for outbox operations

    Methods:
        get_pending: Retrieve pending outbox events
        mark_processing: Mark an outbox event as processing
        mark_completed: Mark an outbox event as completed
        mark_failed: Mark an outbox event as failed
        get_failed: Retrieve failed outbox events

    Example:
        ```python
        outbox_service = OutboxService(db_session)
        events = await outbox_service.get_pending()
        ```
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_pending(
        self,
        limit: int = 100,
    ) -> list[Outbox]:
        """Retrieve pending outbox events.

        Fetches a list of pending outbox events from the database.

        Args:
            limit (int): Maximum number of events to retrieve (default: 100)

        Returns:
            list[Outbox]: List of pending outbox events

        Example:
            ```python
            events = await outbox_service.get_pending()
            ```
        """
        outboxes = await self._outbox_repo.find_many(
            status=OutboxStatus.PENDING,
            order_by=Outbox.created_at,
            limit=limit,
        )

        logger.info(f"get_pending: limit={limit}")
        return list(outboxes)

    async def mark_processing(self, event_id: int) -> None:
        """Mark an outbox event as processing.

        Updates the status of an outbox event to PROCESSING.

        Args:
            event_id (int): ID of the outbox event to mark as processing

        Example:
            ```python
            await outbox_service.mark_processing(123)
            ```
        """
        result = await self._outbox_repo.get(id=event_id)
        if result:
            result.status = OutboxStatus.PROCESSING
            logger.info(f"mark_processing: event_id={event_id}")

    async def mark_completed(
        self,
        event_id: int,
    ) -> None:
        """Mark an outbox event as completed.

        Updates the status of an outbox event to COMPLETED and sets the

        Args:
            event_id (int): ID of the outbox event to mark as completed

        Example:
            ```python
            await outbox_service.mark_completed(123)
            ```
        """
        result = await self._outbox_repo.get(id=event_id)
        if result:
            result.status = OutboxStatus.COMPLETED
            result.processed_at = datetime.now(UTC)
            logger.info(f"mark_completed: event_id={event_id}")

    async def mark_failed(
        self,
        event_id: int,
        error: str,
    ) -> None:
        """Mark an outbox event as failed.

        Updates the status of an outbox event to FAILED and sets the error
        message and retry count.

        Args:
            event_id (int): ID of the outbox event to mark as failed
            error (str): Error message to set

        Example:
            ```python
            await outbox_service.mark_failed(123, "Something went wrong")
            ```
        """
        result = await self._outbox_repo.get(id=event_id)
        if result:
            result.status = OutboxStatus.FAILED
            result.error = error
            result.retry_count += 1
            logger.warning(
                f"mark_failed: event_id={event_id}, error={error or 'unknown'}"
            )

    async def get_failed(self, max_retries: int, limit: int = 100) -> list[Outbox]:
        """Retrieve failed outbox events.

        Fetches a list of failed outbox events from the database.

        Args:
            max_retries (int): Maximum number of retries allowed (default: 3)
            limit (int): Maximum number of events to retrieve (default: 100)

        Returns:
            list[Outbox]: List of failed outbox events

        Example:
            ```python
            events = await outbox_service.get_failed(max_retries=3)
            ```
        """
        result = await self._outbox_repo.find_failed(
            max_retries=max_retries, limit=limit, order_by=Outbox.created_at
        )
        logger.warning(f"get_failed: max_retries={max_retries}, limit={limit}")
        return list(result)


class OutboxTaskService:
    """Outbox service for managing outbox events.

    This service provides functionality for managing outbox events, including
    retrieving, processing, and marking as completed or failed.

    Attributes:
        _db_helper (DatabaseHelper): Database helper for outbox operations
        _es_client_ctx (AsyncElasticsearch): Elasticsearch client context manager
        _doc_mapping (dict[str, tuple[type, type]]): Mapping of entity types to
            model and document classes

    Methods:
        bulk_index: Bulk index entities from outbox events
        process_outbox: Process outbox events
        retry_failed_outbox: Retry failed outbox events

    Example:
        ```python
        outbox_service = OutboxTaskService()
        await outbox_service.process_outbox()
        ```
    """

    def __init__(self) -> None:
        self._db_helper = db_helper
        self._es_client_ctx = es_helper.get_client_ctx
        self._doc_mapping: dict[str, tuple[type, type]] = {
            "task": (Task, TaskDoc),
            "user": (User, UserDoc),
            "group": (UserGroup, UserGroupDoc),
            "comment": (Comment, CommentDoc),
        }

    async def bulk_index(
        self,
        model: Literal["task", "user", "group", "comment"],
        ids: list[int] | None = None,
        batch_size: int = 100,
    ) -> dict[str, Any]:
        """Bulk index entities from outbox events.

        Bulk indexes entities from outbox events based on the provided model.
        Supports bulk indexing of tasks, users, groups, and comments.

        Args:
            model (Literal["task", "user", "group", "comment"]): Entity type to index
            ids (list[int] | None): List of entity IDs to index (default: None)
            batch_size (int): Batch size for indexing (default: 100)

        Returns:
            dict[str, Any]: Dictionary containing indexing results

        Example:
            ```python
            result = await outbox_service.bulk_index(model="task", ids=[123, 456])
            ```
        """
        async with self._db_helper.get_session_ctx() as session:
            async with self._es_client_ctx() as es_client:
                indexer = ElasticsearchIndexer(client=es_client)
                logger.info(
                    f"bulk_index: model={model}, ids={ids}, batch_size={batch_size}"
                )
                return await self._bulk_index_from_session(
                    session=session,
                    indexer=indexer,
                    model=model,
                    ids=ids,
                    batch_size=batch_size,
                )

    async def process_outbox(self, batch_size: int = 100) -> dict[str, Any]:
        """Process outbox events.

        Processes outbox events by marking them as processing, indexing
        entities, and marking them as completed or failed.

        Args:
            batch_size (int): Batch size for indexing (default: 100)

        Returns:
            dict[str, Any]: Dictionary containing processing results

        Example:
            ```python
            result = await outbox_service.process_outbox()
            ```
        """
        async with self._db_helper.get_session_ctx() as session:
            outbox_service = OutboxService(session)
            events = await outbox_service.get_pending(batch_size)
            logger.info(f"process_outbox: Got {len(events)} events")

            if not events:
                logger.info("process_outbox: No events to process")
                return {"processed": 0}

            async with self._es_client_ctx() as es_client:
                indexer = ElasticsearchIndexer(client=es_client)
                await self._process_outbox_batch(
                    session=session,
                    outbox_service=outbox_service,
                    indexer=indexer,
                    events=events,
                )

            logger.info(f"process_outbox: Completed, processed={len(events)}")
            return {"processed": len(events)}

    async def retry_failed_outbox(self, max_retries: int = 3) -> dict[str, Any]:
        """Retry failed outbox events.

        Retries failed outbox events by marking them as pending and incrementing
        the retry count.

        Args:
            max_retries (int): Maximum number of retries allowed (default: 3)

        Returns:
            dict[str, Any]: Dictionary containing retry results

        Example:
            ```python
            result = await outbox_service.retry_failed_outbox()
            ```
        """
        async with self._db_helper.get_session_ctx() as session:
            outbox_service = OutboxService(session)
            events = await outbox_service.get_failed(max_retries)
            result = await self._mark_failed_as_retry(session, events)
            METRICS.OUTBOX_EVENTS_TOTAL.labels(
                entity_type="all", event_type="retry", status="success"
            ).inc(result)
            logger.info(f"process_outbox: retry_failed_outbox: retried={result}")
            return {"retried": result}

    async def _bulk_index_from_session(
        self,
        session: AsyncSession,
        indexer: ElasticsearchIndexer,
        model: Literal["task", "user", "group", "comment"],
        ids: list[int] | None,
        batch_size: int,
    ) -> dict[str, Any]:
        """Bulk index entities from outbox events.

        Bulk indexes entities from outbox events based on the provided model.
        Supports bulk indexing of tasks, users, groups, and comments.

        Args:
            session (AsyncSession): Database session for outbox operations
            indexer (ElasticsearchIndexer): Elasticsearch indexer for outbox operations
            model (Literal["task", "user", "group", "comment"]): Entity type to index
            ids (list[int] | None): List of entity IDs to index (default: None)
            batch_size (int): Batch size for indexing (default: 100)

        Returns:
            dict[str, Any]: Dictionary containing indexing results

        Example:
            ```python
            result = await outbox_service.bulk_index(model="task", ids=[123, 456])
            ```
        """
        mapping = self._doc_mapping.get(model)
        if not mapping:
            logger.error(f"_bulk_index_from_session: unknown model: {model}")
            return {"error": f"Unknown model: {model}"}

        model_class, doc_class = mapping
        stmt: Select[tuple[Any]] = select(model_class)
        if ids:
            stmt = stmt.where(model_class().id.in_(ids))

        result = await session.scalars(stmt.limit(batch_size))
        docs = [doc_class().from_orm(item) for item in result]

        if docs:
            return await indexer.bulk_index(docs)

        logger.info(
            f"_bulk_index_from_session: model={model}, \
                ids={ids}, batch_size={batch_size}"
        )
        return {"errors": False, "items": []}

    async def _process_outbox_batch(
        self,
        session: AsyncSession,
        outbox_service: OutboxService,
        indexer: ElasticsearchIndexer,
        events: list[Outbox],
    ) -> None:
        for event in events:
            await self._process_single_outbox_event(
                session=session,
                outbox_service=outbox_service,
                indexer=indexer,
                event=event,
            )
            logger.info(
                f"_process_outbox_batch: event={event.id}, type={event.event_type}, "
                f"entity={event.entity_type}:{event.entity_id}"
            )

    async def _process_single_outbox_event(
        self,
        session: AsyncSession,
        outbox_service: OutboxService,
        indexer: ElasticsearchIndexer,
        event: Outbox,
    ) -> None:
        with METRICS.OUTBOX_PROCESS_DURATION.labels(
            entity_type=event.entity_type
        ).time():
            try:
                logger.info(
                    f"_process_single_outbox_event: Processing event {event.id}, "
                    f"type={event.event_type}, \
                        entity={event.entity_type}:{event.entity_id}"
                )

                await outbox_service.mark_processing(event.id)
                await session.commit()

                mapping = self._doc_mapping.get(event.entity_type)
                if not mapping:
                    await outbox_service.mark_failed(
                        event.id,
                        f"_process_single_outbox_event: \
                            Unknown entity_type: {event.entity_type}",
                    )
                    await session.commit()
                    logger.warning(
                        f"_process_single_outbox_event: failed event {event.id}, \
                            entity={event.entity_type}:{event.entity_id}"
                    )
                    return

                model_class, doc_class = mapping

                if event.event_type == OutboxEventType.DELETED:
                    await self._delete_document(
                        client=indexer._client,
                        doc_class=doc_class,
                        entity_type=event.entity_type,
                        entity_id=event.entity_id,
                    )
                    logger.info(
                        f"_process_single_outbox_event: \
                            deleted event {event.id}, \
                            entity={event.entity_type}:{event.entity_id}"
                    )
                else:
                    await self._index_document(
                        session=session,
                        indexer=indexer,
                        model_class=model_class,
                        doc_class=doc_class,
                        entity_type=event.entity_type,
                        entity_id=event.entity_id,
                    )
                    logger.info(
                        f"_process_single_outbox_event: indexed event {event.id}, \
                            entity={event.entity_type}:{event.entity_id}"
                    )

                await outbox_service.mark_completed(event.id)
                await session.commit()

                METRICS.OUTBOX_EVENTS_TOTAL.labels(
                    entity_type=event.entity_type,
                    event_type=event.event_type.value,
                    status="success",
                ).inc()

                logger.info(
                    f"_process_single_outbox_event: completed event {event.id}, \
                        entity={event.entity_type}:{event.entity_id}"
                )

            # I use a general Exception instead of dotted ones because:
            # There are many different operations inside the task:
            # SQL, ES, mapping, ORM
            # Point exceptions will not cover all possible errors
            # Celery handles retry itself via
            # autoretry_for=(ConnectionError, TimeoutError)!
            # The main thing is to log the error and mark it as failed
            # for repetition
            except Exception as e:
                METRICS.OUTBOX_EVENTS_TOTAL.labels(
                    entity_type=event.entity_type,
                    event_type=event.event_type.value,
                    status="error",
                ).inc()
                logger.error(
                    f"_process_single_outbox_event: \
                        Error processing event {event.id}: {e}"
                )
                await outbox_service.mark_failed(event.id, str(e))
                await session.commit()
                raise bt_exc.BaseBackgroundError(
                    message=f"_process_single_outbox_event: \
                        Error processing event {event.id}: {e}",
                ) from e

    async def _delete_document(
        self,
        client: AsyncElasticsearch,
        doc_class: type[AsyncDocument],
        entity_type: str,
        entity_id: int,
    ) -> None:
        doc = await doc_class.get(
            id=str(entity_id),
            using=client,
            ignore_status=(404,),
        )
        if doc:
            await doc.delete()
            logger.info(f"_delete_document: deleted {entity_type}:{entity_id}")
        else:
            logger.warning(
                f"_delete_document: no document found for {entity_type}:{entity_id}"
            )

    async def _index_document(
        self,
        session: AsyncSession,
        indexer: ElasticsearchIndexer,
        model_class: type[Base],
        doc_class: type[AsyncDocument],
        entity_type: str,
        entity_id: int,
    ) -> None:
        stmt: Select[tuple[Any]] = select(model_class).where(
            model_class.id == entity_id  # type: ignore[attr-defined]
        )
        result = await session.scalars(stmt)
        entity = result.first()
        if entity:
            doc = doc_class.from_orm(entity)
            await indexer.bulk_index([doc])
            logger.info(f"_index_document: Indexed {entity_type}:{entity_id}")

    async def _mark_failed_as_retry(
        self,
        session: AsyncSession,
        events: list[Outbox],
    ) -> int:
        for event in events:
            event.status = OutboxStatus.PENDING
            event.retry_count += 1
        await session.commit()
        logger.info(f"_mark_failed_as_retry: marked {len(events)} events as pending")
        return len(events)


def get_outbox_service(
    db: AsyncSession = Depends(db_helper.get_session),
) -> OutboxService:
    return OutboxService(db)


outbox_task_service = OutboxTaskService()
