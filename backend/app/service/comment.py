"""Comment service for task-related discussions.

This module provides the CommentService class for managing comments on tasks,
including creation, retrieval, update, and deletion operations.

**Key Components:**
* `CommentService`: Main service class for comment operations;
* `get_comment_service`: FastAPI dependency injection factory.

**Dependencies:**
* `CommentRepository`: Comment data access layer;
* `TaskRepository`: Task data access layer;
* `UnitOfWork`: Transaction management;
* `ElasticsearchIndexer`: Search index management.

**Usage Example:**
    ```python
    from app.service.comment import get_comment_service

    @router.post("/tasks/{task_id}/comments")
    async def create_comment(
        task_id: int,
        content: str,
        comment_svc: CommentService = Depends(get_comment_service),
        current_user: User = Depends(get_current_user)
    ):
        return await comment_svc.create_comment(task_id, content, current_user)
    ```

**Notes:**
- Users can only update or delete their own comments;
- Comments are indexed in Elasticsearch for search functionality;
- Supports nested comments via parent_id parameter.
"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.log import logging
from app.core.metrics import METRICS
from app.db import db_helper
from app.es import ElasticsearchIndexer, get_es_indexer
from app.models import User as UserModel
from app.schemas import CommentRead

from .base import BaseService
from .exceptions import comment_exc
from .transactions.comment import CommentTransaction, get_comment_transaction
from .utils import Indexer

logger = logging.get_logger(__name__)


class CommentService(BaseService):
    """Service for managing comments on tasks.

    Provides functionality for creating, retrieving, updating, and deleting
    comments associated with tasks. Supports threaded comments through
    parent_id references.

    Attributes:
        _db (AsyncSession): SQLAlchemy async session for database operations
        _comment_repository (CommentRepository): Repository for comment operations
        _task_repository (TaskRepository): Repository for task data operations
        _uow (UnitOfWork): Unit of work for transaction management
        _indexer (Indexer): Elasticsearch indexer wrapper for search operations

    Example:
        ```python
        comment_service = CommentService(
            db=session,
            uow=uow,
            indexer=indexer,
            comment_repository=comment_repo,
            task_repository=task_repo
        )
        comment = await comment_service.create_comment(task_id, "Great work!", user)
        ```
    """

    def __init__(
        self,
        db: AsyncSession,
        indexer: ElasticsearchIndexer,
        comment_transaction: CommentTransaction,
    ) -> None:
        """Initialize comment service with dependencies.

        Args:
            db: SQLAlchemy async session for database operations
            uow: Unit of work for transaction management
            indexer: Elasticsearch client for indexing operations
            comment_repository: Repository for comment database operations
            task_repository: Repository for task database operations
        """
        super().__init__(db)
        self._indexer = Indexer(indexer)
        self._comment_transaction = comment_transaction

    async def create_comment(
        self,
        task_id: int,
        content: str,
        current_user: UserModel,
        parent_id: int | None = None,
    ) -> CommentRead:
        """Create a new comment on a task.

        Validates task exists and is active. If parent_id is provided, validates
        parent comment exists and belongs to the same task. Creates comment and
        indexes in Elasticsearch.

        Args:
            task_id: ID of the task to comment on
                Type: int
                Constraints: Must be > 0, task must exist and be active
            content: Comment text content
                Type: str
                Constraints: Non-empty string
            current_user: User creating the comment
                Type: UserModel
            parent_id: ID of parent comment for threaded replies
                Type: int | None
                Defaults to None

        Returns:
            CommentRead: Created comment serialized according to CommentRead schema

        Raises:
            task_exc.TaskNotFound: When task does not exist or is inactive
            comment_exc.NotFoundParentError: When parent comment not found or
                belongs to different task

        Example:
            ```python
            comment = await comment_svc.create_comment(
                task_id=123,
                content="Great progress on this task!",
                current_user=user
            )
            ```
        """
        comment = await self._comment_transaction.create_comment(
            task_id=task_id,
            content=content,
            current_user=current_user,
            parent_id=parent_id,
        )

        METRICS.SOCIAL_ACTIONS_TOTAL.labels(
            type="comment", action="create", status="success"
        ).inc()
        await self._indexer.index(comment)

        logger.info(
            "Comment created: id={comment_id}, task_id={task_id}, user_id={user_id}",
            comment_id=comment.id,
            task_id=task_id,
            user_id=current_user.id,
        )
        return CommentRead.model_validate(comment)

    async def get_task_comments(
        self,
        task_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> list[CommentRead]:
        """Retrieve all comments for a specific task.

        Fetches comments associated with a task with pagination support.
        Results are ordered by creation time (newest first).

        Args:
            task_id: ID of the task to get comments for
                Type: int
                Constraints: Must be > 0
            limit: Maximum number of comments to return
                Type: int
                Defaults to 50
            offset: Number of comments to skip for pagination
                Type: int
                Defaults to 0

        Returns:
            list[CommentRead]: List of comments serialized according to
                CommentRead schema

        Raises:
            None

        Example:
            ```python
            comments = await comment_svc.get_task_comments(
                task_id=123,
                limit=20,
                offset=0
            )
            ```
        """
        comments = await self._comment_repo.find_many(
            task_id=task_id,
            limit=limit,
            offset=offset,
        )

        METRICS.SOCIAL_ACTIONS_TOTAL.labels(
            type="comment", action="view", status="success"
        ).inc()
        logger.info(
            "Task comments retrieved: task_id={task_id}, count={count}",
            task_id=task_id,
            count=len(comments),
        )
        return [CommentRead.model_validate(comment) for comment in comments]

    async def get_comment(
        self,
        comment_id: int,
    ) -> CommentRead:
        """Retrieve a specific comment by ID.

        Fetches a single comment regardless of its task association.

        Args:
            comment_id: ID of the comment to retrieve
                Type: int
                Constraints: Must be > 0

        Returns:
            CommentRead: Comment serialized according to CommentRead schema

        Raises:
            comment_exc.CommentNotFoundError: When comment does not exist

        Example:
            ```python
            comment = await comment_svc.get_comment(comment_id=456)
            ```
        """
        comment = await self._comment_repo.get(
            id=comment_id,
        )
        if not comment:
            raise comment_exc.CommentNotFoundError(
                message=f"Comment {comment_id} not found"
            )
        return CommentRead.model_validate(comment)

    async def update_comment(
        self,
        comment_id: int,
        content: str,
        current_user: UserModel,
    ) -> CommentRead:
        """Update an existing comment.

        Validates comment exists and user owns the comment. Updates content
        and re-indexes in Elasticsearch.

        Args:
            comment_id: ID of the comment to update
                Type: int
                Constraints: Must be > 0, comment must exist
            content: New comment text content
                Type: str
                Constraints: Non-empty string
            current_user: User attempting to update the comment
                Type: UserModel

        Returns:
            CommentRead: Updated comment serialized according to CommentRead schema

        Raises:
            comment_exc.CommentNotFoundError: When comment does not exist
            comment_exc.ForbiddenError: When user does not own the comment

        Example:
            ```python
            comment = await comment_svc.update_comment(
                comment_id=456,
                content="Updated comment text",
                current_user=user
            )
            ```
        """
        comment = await self._comment_transaction.update_comment(
            comment_id=comment_id,
            content=content,
            current_user=current_user,
        )

        METRICS.SOCIAL_ACTIONS_TOTAL.labels(
            action="comment_update", type="comment", status="success"
        ).inc()
        await self._indexer.index(comment)

        logger.info(
            "Comment updated: id={comment_id}, user_id={user_id}",
            comment_id=comment_id,
            user_id=current_user.id,
        )
        return CommentRead.model_validate(comment)

    async def delete_comment(
        self,
        comment_id: int,
        current_user: UserModel,
    ) -> None:
        """Delete a comment.

        Validates comment exists and user owns the comment. Removes comment
        from database and deletes from Elasticsearch index.

        Args:
            comment_id: ID of the comment to delete
                Type: int
                Constraints: Must be > 0, comment must exist
            current_user: User attempting to delete the comment
                Type: UserModel

        Returns:
            None

        Raises:
            comment_exc.CommentNotFoundError: When comment does not exist
            comment_exc.ForbiddenError: When user does not own the comment

        Example:
            ```python
            await comment_svc.delete_comment(comment_id=456, current_user=user)
            ```
        """
        await self._comment_transaction.delete_comment(
            comment_id=comment_id,
            current_user=current_user,
        )

        METRICS.SOCIAL_ACTIONS_TOTAL.labels(
            type="comment", action="delete", status="success"
        ).inc()
        await self._indexer.delete({"type": "comment", "id": comment_id})

        logger.info(
            "Comment deleted: id={comment_id}, user_id={user_id}",
            comment_id=comment_id,
            user_id=current_user.id,
        )


def get_comment_service(
    db: AsyncSession = Depends(db_helper.get_session),
    indexer: ElasticsearchIndexer = Depends(get_es_indexer),
    comment_transaction: CommentTransaction = Depends(get_comment_transaction),
) -> CommentService:
    """Create CommentService instance with dependency injection.

    Factory function for FastAPI dependency injection that creates and configures
    a CommentService instance with all required dependencies.

    Args:
        db: Database session from FastAPI dependency injection.
            Type: AsyncSession.
        uow: Unit of work from FastAPI dependency injection.
            Type: UnitOfWork.
        indexer: Elasticsearch client from FastAPI dependency injection.
            Type: ElasticsearchIndexer.
        comment_repository: Comment repository from FastAPI dependency injection.
            Type: CommentRepository.
        task_repository: Task repository from FastAPI dependency injection.
            Type: TaskRepository.

    Returns:
        CommentService: Configured comment service instance

    Example:
        ```python
        @router.get("/tasks/{task_id}/comments")
        async def get_comments(
            task_id: int,
            comment_svc: CommentService = Depends(get_comment_service)
        ):
            return await comment_svc.get_task_comments(task_id)
        ```
    """
    return CommentService(
        db=db,
        indexer=indexer,
        comment_transaction=comment_transaction,
    )
