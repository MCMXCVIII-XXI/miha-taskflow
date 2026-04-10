"""Bulk operations service for efficient data processing and indexing.

This service provides functionality for bulk operations including
massive data indexing to Elasticsearch for improved performance
during large-scale data operations.
"""

from typing import Any

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import db_helper
from app.es import ElasticsearchIndexer, get_es_indexer
from app.models import Comment as CommentModel
from app.models import Task as TaskModel
from app.models import User as UserModel
from app.models import UserGroup as UserGroupModel

from .base import BaseService


class BulkService(BaseService):
    """Provides bulk operations for efficient data processing and indexing.

    This service implements bulk indexing operations for various entity types
    to Elasticsearch, enabling efficient handling of large datasets during
    initial indexing, data migrations, or bulk updates.

    Attributes:
        _db (AsyncSession): Database session for bulk operations
        _indexer (ElasticsearchIndexer): Elasticsearch indexer for bulk operations
    """

    def __init__(self, db: AsyncSession, indexer: ElasticsearchIndexer) -> None:
        """Initialize bulk service with database and Elasticsearch indexer.

        Args:
            db (AsyncSession): Database session for bulk operations
            indexer (ElasticsearchIndexer): Elasticsearch indexer for bulk operations
        """
        super().__init__(db)
        self._indexer = indexer

    async def bulk_index_tasks(self, tasks: list[TaskModel]) -> dict[str, Any]:
        """Perform bulk indexing of tasks to Elasticsearch.

        Efficiently indexes multiple task entities to Elasticsearch in a single
        operation for improved performance during large-scale data operations.

        Args:
            tasks (list[TaskModel]): List of task models to index

        Returns:
            dict[str, any]: Indexing operation results and statistics
        """
        return await self._indexer.bulk_index_tasks(tasks)

    async def bulk_index_users(self, users: list[UserModel]) -> dict[str, Any]:
        """Perform bulk indexing of users to Elasticsearch.

        Efficiently indexes multiple user entities to Elasticsearch in a single
        operation for improved performance during large-scale data operations.

        Args:
            users (list[UserModel]): List of user models to index

        Returns:
            dict[str, any]: Indexing operation results and statistics
        """
        return await self._indexer.bulk_index_users(users)

    async def bulk_index_groups(self, groups: list[UserGroupModel]) -> dict[str, Any]:
        """Perform bulk indexing of groups to Elasticsearch.

        Efficiently indexes multiple group entities to Elasticsearch in a single
        operation for improved performance during large-scale data operations.

        Args:
            groups (list[UserGroupModel]): List of group models to index

        Returns:
            dict[str, any]: Indexing operation results and statistics
        """
        return await self._indexer.bulk_index_groups(groups)

    async def bulk_index_comments(self, comments: list[CommentModel]) -> dict[str, Any]:
        """Perform bulk indexing of comments to Elasticsearch.

        Efficiently indexes multiple comment entities to Elasticsearch in a single
        operation for improved performance during large-scale data operations.

        Args:
            comments (list[CommentModel]): List of comment models to index

        Returns:
            dict[str, any]: Indexing operation results and statistics
        """
        return await self._indexer.bulk_index_comments(comments)


def get_bulk_service(
    db: AsyncSession = Depends(db_helper.get_session),
    indexer: ElasticsearchIndexer = Depends(get_es_indexer),
) -> BulkService:
    """FastAPI dependency for BulkService instantiation.

    Creates and configures BulkService instance with required dependencies
    for handling bulk indexing operations.

    Args:
        db (AsyncSession): Database session from dependency injection
        indexer (ElasticsearchIndexer): Elasticsearch indexer from dependency injection

    Returns:
        BulkService: Configured bulk operations service instance
    """
    return BulkService(db, indexer)
