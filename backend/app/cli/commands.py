"""Script for reindexing all data to Elasticsearch."""

from typing import TYPE_CHECKING

from app.es.reindex_service import ReindexService

from app.cli.manage import app
from app.core.log import get_logger
from app.db import Base, db_helper
from app.es import get_es_indexer
from app.indexes import CommentDoc, NotificationDoc, TaskDoc, UserDoc, UserGroupDoc
from app.models import Comment, Notification, Task, User, UserGroup

if TYPE_CHECKING:
    from typing import TypeVar

    ModelType = TypeVar("ModelType", bound=Base)
    DocType = TypeVar("DocType")

logger = get_logger(__name__)


@app.command()
async def reindex_all(batch_size: int = 100) -> None:
    """Reindex all data to Elasticsearch."""
    logger.info("Starting full reindex process")

    async with db_helper.get_session_ctx() as session:
        indexer = get_es_indexer()
        service = ReindexService(session, indexer)

        await service.reindex_model(session, User, UserDoc, batch_size)
        await service.reindex_model(session, UserGroup, UserGroupDoc, batch_size)
        await service.reindex_model(session, Task, TaskDoc, batch_size)
        await service.reindex_model(session, Comment, CommentDoc, batch_size)
        await service.reindex_model(session, Notification, NotificationDoc, batch_size)

    logger.info("Full reindex process completed")


@app.command()
async def reindex_tasks(batch_size: int = 100) -> None:
    """Reindex only tasks to Elasticsearch."""
    logger.info("Starting task reindex process")

    async with db_helper.get_session_ctx() as session:
        indexer = get_es_indexer()
        service = ReindexService(session, indexer)
        await service.reindex_model(Task, TaskDoc, batch_size)

    logger.info("Task reindex process completed")


@app.command()
async def reindex_users(batch_size: int = 100) -> None:
    """Reindex only users to Elasticsearch."""
    logger.info("Starting user reindex process")

    async with db_helper.get_session_ctx() as session:
        indexer = get_es_indexer()
        service = ReindexService(session, indexer)
        await service.reindex_model(User, UserDoc, batch_size)

    logger.info("User reindex process completed")
