from typing import Any, Literal, TypedDict

from elasticsearch import exceptions
from elasticsearch.dsl import AsyncDocument

from app.db import Base
from app.es.exceptions import es_exc
from app.es.indexer import ElasticsearchIndexer
from app.models import Comment as CommentModel
from app.models import Notification as NotificationModel
from app.models import Task as TaskModel
from app.models import User as UserModel
from app.models import UserGroup as UserGroupModel

ContextIdType = Literal["task", "user", "group", "comment", "notification"]


class Context(TypedDict):
    type: ContextIdType
    id: int


class Indexer:
    def __init__(self, indexer: ElasticsearchIndexer):
        self._indexer = indexer

    async def bulk_index_tasks(self, tasks: list[TaskModel]) -> dict[str, Any]:
        """Bulk index multiple tasks to Elasticsearch."""
        return await self._indexer.bulk_index_tasks(tasks)

    async def bulk_index_users(self, users: list[UserModel]) -> dict[str, Any]:
        """Bulk index multiple users to Elasticsearch."""
        return await self._indexer.bulk_index_users(users)

    async def bulk_index_groups(self, groups: list[UserGroupModel]) -> dict[str, Any]:
        """Bulk index multiple groups to Elasticsearch."""
        return await self._indexer.bulk_index_groups(groups)

    async def bulk_index_comments(self, comments: list[CommentModel]) -> dict[str, Any]:
        """Bulk index multiple comments to Elasticsearch."""
        return await self._indexer.bulk_index_comments(comments)

    async def _index(self, model: Base) -> AsyncDocument | None:
        model_name = model.__class__.__name__
        if model_name == TaskModel.__name__:
            return await self._indexer.index_task(model)  # type: ignore[arg-type]
        elif model_name == UserModel.__name__:
            return await self._indexer.index_user(model)  # type: ignore[arg-type]
        elif model_name == UserGroupModel.__name__:
            return await self._indexer.index_group(model)  # type: ignore[arg-type]
        elif model_name == CommentModel.__name__:
            return await self._indexer.index_comment(model)  # type: ignore[arg-type]
        elif model_name == NotificationModel.__name__:
            return await self._indexer.index_notification(model)  # type: ignore[arg-type]
        else:
            return None

    async def _delete(self, context: Context) -> bool:
        if context["type"] == "task":
            return await self._indexer.delete_task(context["id"])
        elif context["type"] == "user":
            return await self._indexer.delete_user(context["id"])
        elif context["type"] == "group":
            return await self._indexer.delete_group(context["id"])
        elif context["type"] == "comment":
            return await self._indexer.delete_comment(context["id"])
        elif context["type"] == "notification":
            return await self._indexer.delete_notification(context["id"])

    async def index(self, model: Base) -> AsyncDocument | None:
        """Public: index model → ES."""
        try:
            return await self._index(model)
        except exceptions.ConflictError as e:
            raise es_exc.ElasticsearchDocumentConflictError(
                f"Document conflict for {model.__class__.__name__}",
                details={"raw": e.info},
            ) from e
        except exceptions.NotFoundError as e:
            raise es_exc.ElasticsearchDocumentNotFoundError(
                f"Not found: {model.__class__.__name__}",
                details={"raw": e.info if hasattr(e, "info") else str(e)},
            ) from e
        except exceptions.BadRequestError as e:
            raise es_exc.ElasticsearchBadRequestError(
                f"Bad request: {model.__class__.__name__}",
                details={"raw": e.info if hasattr(e, "info") else str(e)},
            ) from e

    async def delete(self, context: Context) -> None:
        """Public: delete by type+id."""
        try:
            deleted = await self._delete(context)
            if not deleted:
                type_, id_ = context["type"], context["id"]
                raise es_exc.ElasticsearchDocumentNotFoundError(
                    f"{type_.title()} {id_} not found in ES"
                )
        except exceptions.NotFoundError as e:
            raise es_exc.ElasticsearchDocumentNotFoundError(
                f"Not found: {context['type']} {context['id']}",
                details={"raw": e.info if hasattr(e, "info") else str(e)},
            ) from e
        except exceptions.BadRequestError as e:
            raise es_exc.ElasticsearchBadRequestError(
                f"Failed to delete {context['type']} {context['id']}",
                details={"raw": str(e)},
            ) from e
