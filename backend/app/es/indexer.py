from collections.abc import Sequence
from typing import Any

from elasticsearch import AsyncElasticsearch
from elasticsearch.exceptions import BadRequestError
from fastapi import Depends

from app.core.log import get_logger
from app.documents import (
    CommentDoc,
    NotificationDoc,
    TaskDoc,
    UserDoc,
    UserGroupDoc,
)
from app.es import es_helper
from app.models import Comment as CommentModel
from app.models import Notification as NotificationModel
from app.models import Task as TaskModel
from app.models import User as UserModel
from app.models import UserGroup as UserGroupModel

from .exceptions import es_exc

logger = get_logger(__name__)


class ElasticsearchIndexer:
    """Elasticsearch indexer for full-text search functionality.

    This class provides methods to index application models into Elasticsearch
    for fast full-text search capabilities. It converts SQLAlchemy models
    to Elasticsearch documents and manages the indexing process.

    Attributes:
        _client (AsyncElasticsearch): Elasticsearch client for index operations

    Note:
        All indexing operations are asynchronous and should be called
        from async contexts. Documents are automatically synced with
        database models through ORM conversion methods.
    """

    def __init__(self, client: AsyncElasticsearch):
        """Initialize Elasticsearch indexer with client instance.

        Args:
            client (AsyncElasticsearch): Configured Elasticsearch client
        """
        self._client = client

    async def index_task(self, task: TaskModel) -> TaskDoc:
        """Index a task model into Elasticsearch.

        Converts a Task SQLAlchemy model to TaskDoc and saves it
        to the Elasticsearch index for search functionality.

        Args:
            task (TaskModel): Task model to index

        Returns:
            TaskDoc: Indexed Elasticsearch document
        """
        doc = TaskDoc.from_orm(task)
        await doc.save(using=self._client, refresh=True)
        return doc

    async def index_user(self, user: UserModel) -> UserDoc:
        """Index a user model into Elasticsearch.

        Converts a User SQLAlchemy model to UserDoc and saves it
        to the Elasticsearch index for search functionality.

        Args:
            user (UserModel): User model to index

        Returns:
            UserDoc: Indexed Elasticsearch document
        """
        doc = UserDoc.from_orm(user)
        await doc.save(using=self._client, refresh=True)
        return doc

    async def index_group(self, group: UserGroupModel) -> UserGroupDoc:
        """Index a group model into Elasticsearch.

        Converts a UserGroup SQLAlchemy model to UserGroupDoc and saves it
        to the Elasticsearch index for search functionality.

        Args:
            group (UserGroupModel): Group model to index

        Returns:
            UserGroupDoc: Indexed Elasticsearch document
        """
        doc = UserGroupDoc.from_orm(group)
        await doc.save(using=self._client, refresh=True)
        return doc

    async def index_comment(self, comment: CommentModel) -> CommentDoc:
        """Index a comment model into Elasticsearch.

        Converts a Comment SQLAlchemy model to CommentDoc and saves it
        to the Elasticsearch index for search functionality.

        Args:
            comment (CommentModel): Comment model to index

        Returns:
            CommentDoc: Indexed Elasticsearch document
        """
        doc = CommentDoc.from_orm(comment)
        await doc.save(using=self._client, refresh=True)
        return doc

    async def bulk_index_tasks(self, tasks: list[TaskModel]) -> dict[str, Any]:
        """Bulk index multiple tasks to Elasticsearch."""
        docs = []
        for task in tasks:
            try:
                doc = TaskDoc.from_orm(task)
                docs.append(doc)
            except BadRequestError as e:
                logger.error(
                    f"Error creating TaskDoc for task \
                        {getattr(task, 'id', 'unknown')}: {e}"
                )
                raise es_exc.ElasticsearchBadRequestError(
                    message=f"Error creating TaskDoc for task \
                        {getattr(task, 'id', 'unknown')}: {e}"
                ) from e

        if docs:
            logger.info(f"Bulk indexing {len(docs)} tasks")
            return await self.bulk_index(docs)
        return {"errors": False, "items": []}

    async def bulk_index_users(self, users: list[UserModel]) -> dict[str, Any]:
        """Bulk index multiple users to Elasticsearch."""
        docs = []
        for user in users:
            try:
                doc = UserDoc.from_orm(user)
                docs.append(doc)
            except BadRequestError as e:
                logger.error(
                    f"Error creating UserDoc for user \
                        {getattr(user, 'id', 'unknown')}: {e}"
                )
                raise es_exc.ElasticsearchBadRequestError(
                    message=f"Error creating UserDoc for user \
                        {getattr(user, 'id', 'unknown')}: {e}"
                ) from e

        if docs:
            logger.info(f"Bulk indexing {len(docs)} users")
            return await self.bulk_index(docs)
        return {"errors": False, "items": []}

    async def bulk_index_groups(self, groups: list[UserGroupModel]) -> dict[str, Any]:
        """Bulk index multiple groups to Elasticsearch."""
        docs = []
        for group in groups:
            try:
                doc = UserGroupDoc.from_orm(group)
                docs.append(doc)
            except BadRequestError as e:
                logger.error(
                    f"Error creating UserGroupDoc for group \
                        {getattr(group, 'id', 'unknown')}: {e}"
                )
                raise es_exc.ElasticsearchBadRequestError(
                    message=f"Error creating UserGroupDoc for group \
                        {getattr(group, 'id', 'unknown')}: {e}"
                ) from e

        if docs:
            logger.info(f"Bulk indexing {len(docs)} groups")
            return await self.bulk_index(docs)
        return {"errors": False, "items": []}

    async def bulk_index_comments(self, comments: list[CommentModel]) -> dict[str, Any]:
        """Bulk index multiple comments to Elasticsearch."""
        docs = []
        for comment in comments:
            try:
                doc = CommentDoc.from_orm(comment)
                docs.append(doc)
            except BadRequestError as e:
                logger.error(
                    f"Error creating CommentDoc for comment \
                        {getattr(comment, 'id', 'unknown')}: {e}"
                )
                raise es_exc.ElasticsearchBadRequestError(
                    message=f"Error creating CommentDoc for comment \
                        {getattr(comment, 'id', 'unknown')}: {e}"
                ) from e

        if docs:
            logger.info(f"Bulk indexing {len(docs)} comments")
            return await self.bulk_index(docs)
        return {"errors": False, "items": []}

    async def index_notification(
        self, notification: NotificationModel
    ) -> NotificationDoc:
        """Notification → NotificationDoc.save()"""
        doc = NotificationDoc.from_orm(notification)
        await doc.save(using=self._client, refresh=True)
        return doc

    async def delete_task(self, task_id: int) -> bool:
        """Delete task by ID."""
        doc = await TaskDoc.get(
            id=str(task_id), using=self._client, ignore_status=(404,)
        )
        if doc:
            await doc.delete()
            return True
        return False

    async def delete_user(self, user_id: int) -> bool:
        """Delete user by ID."""
        doc = await UserDoc.get(
            id=str(user_id), using=self._client, ignore_status=(404,)
        )
        if doc:
            await doc.delete()
            return True
        return False

    async def delete_group(self, group_id: int) -> bool:
        """Delete group by ID."""
        doc = await UserGroupDoc.get(
            id=str(group_id), using=self._client, ignore_status=(404,)
        )
        if doc:
            await doc.delete()
            return True
        return False

    async def delete_comment(self, comment_id: int) -> bool:
        """Delete comment by ID."""
        doc = await CommentDoc.get(
            id=str(comment_id), using=self._client, ignore_status=(404,)
        )
        if doc:
            await doc.delete()
            return True
        return False

    async def delete_notification(self, notification_id: int) -> bool:
        """Delete notification by ID."""
        doc = await NotificationDoc.get(
            id=str(notification_id), using=self._client, ignore_status=(404,)
        )
        if doc:
            await doc.delete()
            return True
        return False

    async def bulk_index(
        self,
        docs: Sequence[TaskDoc | UserDoc | UserGroupDoc | CommentDoc | NotificationDoc],
    ) -> dict[str, Any]:
        """Unified bulk index for all document types."""
        actions = []
        for doc in docs:
            if doc:
                action = {"index": {"_index": doc.Index.name, "_id": str(doc.id)}}
                actions.append(action)
                actions.append(doc.to_dict(True))

        stats = await self._client.bulk(body=actions, refresh=True)
        return stats.body

    async def refresh_all(self) -> None:
        """Refresh all indices."""
        await self._client.indices.refresh()


def get_es_indexer(
    es: AsyncElasticsearch = Depends(es_helper.get_client),
) -> ElasticsearchIndexer:
    return ElasticsearchIndexer(client=es)
