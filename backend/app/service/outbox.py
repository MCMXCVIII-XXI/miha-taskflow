from datetime import UTC
from typing import Any, Literal

from elasticsearch import AsyncElasticsearch
from elasticsearch.dsl import AsyncDocument
from fastapi import Depends
from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.background.exceptions import bt_exc
from app.core.log import logging
from app.db import Base, db_helper
from app.es.client import es_helper
from app.es.indexer import ElasticsearchIndexer
from app.indexes import CommentDoc, TaskDoc, UserDoc, UserGroupDoc
from app.models import (
    Comment,
    Task,
    User,
    UserGroup,
)
from app.models.outbox import Outbox
from app.schemas.enum import OutboxEventType, OutboxStatus

from .base import BaseService
from .query_db import OutboxQueries

logger = logging.get_logger(__name__)


class OutboxService(BaseService):
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._outbox_queries = OutboxQueries()

    async def publish(
        self,
        event_type: OutboxEventType,
        entity_type: str,
        entity_id: int,
        payload: dict[str, Any] | None = None,
    ) -> Outbox:
        event = Outbox(
            event_type=event_type.value,
            entity_type=entity_type,
            entity_id=entity_id,
            payload=payload,
            status=OutboxStatus.PENDING,
        )
        self._db.add(event)
        logger.info(
            f"publish: event_type={event_type}, \
                entity_type={entity_type}, entity_id={entity_id}"
        )
        return event

    async def get_pending(
        self,
        limit: int = 100,
    ) -> list[Outbox]:
        result = await self._db.scalars(
            self._outbox_queries.get_outbox(status=OutboxStatus.PENDING)
            .order_by(Outbox.created_at)
            .limit(limit)
        )
        logger.info(f"get_pending: limit={limit}")
        return list(result.all())

    async def mark_processing(self, event_id: int) -> None:
        result = await self._db.scalar(self._outbox_queries.get_outbox(id=event_id))
        if result:
            result.status = OutboxStatus.PROCESSING
            logger.info(f"mark_processing: event_id={event_id}")

    async def mark_completed(
        self,
        event_id: int,
    ) -> None:
        from datetime import datetime

        result = await self._db.scalar(self._outbox_queries.get_outbox(id=event_id))
        if result:
            result.status = OutboxStatus.COMPLETED
            result.processed_at = datetime.now(UTC)
            logger.info(f"mark_completed: event_id={event_id}")

    async def mark_failed(
        self,
        event_id: int,
        error: str,
    ) -> None:
        result = await self._db.scalar(self._outbox_queries.get_outbox(id=event_id))
        if result:
            result.status = OutboxStatus.FAILED
            result.error = error
            result.retry_count += 1
            logger.warning(
                f"mark_failed: event_id={event_id}, error={error or 'unknown'}"
            )

    async def get_failed(self, max_retries: int, limit: int = 100) -> list[Outbox]:
        result = await self._db.scalars(
            select(Outbox)
            .where(
                Outbox.status == OutboxStatus.FAILED,
                Outbox.retry_count < max_retries,
            )
            .order_by(Outbox.created_at)
            .limit(limit)
        )
        logger.warning(f"get_failed: max_retries={max_retries}, limit={limit}")
        return list(result.all())


class OutboxTaskService:
    def __init__(self) -> None:
        self._es_client_ctx = es_helper.get_client_ctx
        self._doc_mapping: dict[str, tuple[type, type]] = {
            "task": (Task, TaskDoc),
            "user": (User, UserDoc),
            "group": (UserGroup, UserGroupDoc),
            "comment": (Comment, CommentDoc),
        }

    @property
    def _session_factory(self):
        """Lazy session_factory to support test environment configuration."""
        return db_helper.session_factory

    async def bulk_index(
        self,
        model: Literal["task", "user", "group", "comment"],
        ids: list[int] | None = None,
        batch_size: int = 100,
    ) -> dict[str, Any]:
        async with self._session_factory() as session:
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

        async with self._session_factory() as session:
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
        async with self._session_factory() as session:
            outbox_service = OutboxService(session)
            events = await outbox_service.get_failed(max_retries)
            result = await self._mark_failed_as_retry(session, events)
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
        try:
            logger.info(
                f"_process_single_outbox_event: Processing event {event.id}, "
                f"type={event.event_type}, entity={event.entity_type}:{event.entity_id}"
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
            logger.error(
                f"_process_single_outbox_event: Error processing event {event.id}: {e}"
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
