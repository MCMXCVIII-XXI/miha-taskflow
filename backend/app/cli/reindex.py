"""Service for reindexing data to Elasticsearch."""

from typing import TYPE_CHECKING, Any, TypeVar, cast

from sqlalchemy import func, select
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.log import get_logger
from app.db import Base
from app.es import ElasticsearchIndexer
from app.es.exceptions import es_exc
from app.models import Task

if TYPE_CHECKING:
    DocType = TypeVar("DocType")
    ModelType = TypeVar("ModelType", bound=Base)


logger = get_logger(__name__)


class ReindexService:
    def __init__(self, session: AsyncSession, indexer: ElasticsearchIndexer) -> None:
        self.session = session
        self.indexer = indexer

    async def reindex_model(
        self,
        model_class: type[Base],
        doc_class: type[Any],
        batch_size: int = 100,
    ) -> None:
        """Reindex all instances of a model to Elasticsearch."""
        logger.info(f"Starting reindex of {model_class.__name__}")

        total_count = await self._count_records(model_class)

        logger.info(f"Total {model_class.__name__} records: {total_count}")
        if total_count == 0:
            logger.info(f"No {model_class.__name__} records to index")
            return

        offset = 0
        processed = 0

        while offset < total_count:
            instances = await self._fetch_batch(model_class, offset, batch_size)
            if not instances:
                break

            docs = self._create_docs(model_class, doc_class, instances)
            if not docs:
                offset += batch_size
                continue

            indexed_count = await self._index_batch(
                model_class, doc_class, docs, instances, offset, batch_size
            )
            processed += indexed_count

            offset += batch_size

        logger.info(
            f"Finished reindexing {model_class.__name__}: "
            f"{processed}/{total_count} records indexed"
        )

    async def _count_records(
        self,
        model_class: type[Base],
    ) -> int:
        """Count total records of model_class."""
        try:
            total_count_result = await self.session.execute(
                select(func.count()).select_from(model_class)
            )
            return total_count_result.scalar_one()
        except DBAPIError as e:
            logger.error(f"Database error counting {model_class.__name__}: {e}")
            raise es_exc.ElasticsearchConnectionError(
                message=f"Database error counting {model_class.__name__}: {e}"
            ) from e

    async def _fetch_batch(
        self,
        model_class: type[Base],
        offset: int,
        batch_size: int,
    ) -> list[Base]:
        if model_class == Task:
            stmt = (
                select(Task)
                .options(
                    selectinload(Task.group),
                    selectinload(Task.assignees),
                    selectinload(Task.comments),
                )
                .offset(offset)
                .limit(batch_size)
            )
        else:
            stmt = cast(
                Any,
                select(model_class).offset(offset).limit(batch_size),
            )

        try:
            result = await self.session.execute(stmt)
            instances: list[Base] = list(result.scalars().all())
            return instances
        except DBAPIError as e:
            logger.error(
                f"Database error fetching batch for {model_class.__name__}: {e}"
            )
            raise es_exc.ElasticsearchConnectionError(
                message=f"Database error fetching batch for {model_class.__name__}: {e}"
            ) from e

    def _create_docs(
        self,
        model_class: type[Base],
        doc_class: type[Any],
        instances: list[Base],
    ) -> list[Any]:
        """Create document objects from model instances."""
        docs = []
        for instance in instances:
            try:
                doc = doc_class.from_orm(instance)
                docs.append(doc)
            except (ValueError, TypeError, AttributeError) as e:
                logger.error(
                    f"Data mapping error creating {doc_class.__name__} "
                    f"for {model_class.__name__} "
                    f"{getattr(instance, 'id', 'unknown')}: {e}"
                )
                continue
        return docs

    async def _index_batch(
        self,
        model_class: type[Base],
        doc_class: type[Any],
        docs: list[Any],
        instances: list[Base],
        offset: int,
        batch_size: int,
    ) -> int:
        """Index a batch of documents."""
        if not docs:
            return 0

        try:
            stats = await self.indexer.bulk_index(docs)
            count = len(docs)
            logger.info(
                f"Indexed batch {offset}-{offset + len(instances)} ({count} documents)"
            )
            if stats.get("errors"):
                logger.warning(f"Bulk index had errors: {stats}")
            return count
        except Exception as e:
            logger.error(f"Elasticsearch transport or API error indexing batch: {e}")
            raise es_exc.ElasticsearchBulkError(
                message=f"Elasticsearch transport or API error indexing batch: {e}"
            ) from e
