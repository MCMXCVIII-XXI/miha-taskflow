from fastapi import APIRouter, Depends, Query, status

from app.core.permission import require_permissions_db
from app.examples.comment_examples import CommentExamples
from app.models import User as UserModel
from app.schemas import CommentCreate, CommentRead, CommentUpdate
from app.service import CommentService, get_comment_service

router = APIRouter(tags=["comments"])


@router.post(
    "/tasks/{task_id}/comments",
    response_model=CommentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create comment",
    description="""
    Create a new comment for a task.

    **Permissions required:** GROUP_MEMBER

    **Request body:**
    - `content` (required, 1-1000 chars): Comment text
    - `parent_id` (optional): Parent comment ID for threaded replies

    **Returns:** Created comment with ID and timestamp.
    """,
    responses={
        201: {
            "description": "Comment created successfully",
            "content": {
                "application/json": {"example": CommentExamples.CREATE_SUCCESS}
            },
        },
        404: {"description": "Task not found"},
    },
)
async def create_comment(
    task_id: int,
    comment_in: CommentCreate,
    current_user: UserModel = Depends(require_permissions_db("comment:create:own")),
    comment_service: CommentService = Depends(get_comment_service),
) -> CommentRead:
    """Create a new comment for a task."""
    return await comment_service.create_comment(
        task_id=task_id,
        content=comment_in.content,
        current_user=current_user,
        parent_id=comment_in.parent_id,
    )


@router.get(
    "/tasks/{task_id}/comments",
    response_model=list[CommentRead],
    status_code=status.HTTP_200_OK,
    summary="Get task comments",
    description="""
    Get comments for a specific task with pagination.

    **Permissions required:** GROUP_MEMBER

    **Query parameters:**
    - `limit` (default: 50): Max comments to return
    - `offset` (default: 0): Number of comments to skip

    **Returns:** List of comments sorted by created_at (oldest first).
    """,
    responses={
        200: {
            "description": "Comments retrieved",
            "content": {"application/json": {"example": CommentExamples.GET_ALL}},
        },
    },
)
async def get_task_comments(
    task_id: int,
    limit: int = Query(50, ge=1, le=100, description="Max comments to return"),
    offset: int = Query(0, ge=0, description="Number of comments to skip"),
    current_user: UserModel = Depends(require_permissions_db("comment:view:any")),
    comment_service: CommentService = Depends(get_comment_service),
) -> list[CommentRead]:
    """Get comments for a specific task with pagination."""
    return await comment_service.get_task_comments(task_id, limit, offset)


@router.get(
    "/comments/{comment_id}",
    response_model=CommentRead,
    status_code=status.HTTP_200_OK,
    summary="Get comment",
    description="""
    Get a single comment by ID.

    **Permissions required:** GROUP_MEMBER
    """,
    responses={
        200: {
            "description": "Comment retrieved",
            "content": {"application/json": {"example": CommentExamples.GET_BY_ID}},
        },
        404: {
            "description": "Comment not found",
            "content": {"application/json": {"example": CommentExamples.NOT_FOUND}},
        },
    },
)
async def get_comment(
    comment_id: int,
    current_user: UserModel = Depends(require_permissions_db("comment:view:any")),
    comment_service: CommentService = Depends(get_comment_service),
) -> CommentRead:
    """Get a single comment by ID."""
    return await comment_service.get_comment(comment_id)


@router.patch(
    "/comments/{comment_id}",
    response_model=CommentRead,
    status_code=status.HTTP_200_OK,
    summary="Update comment",
    description="""
    Update a comment's content.

    **Permissions required:** COMMENT_AUTHOR only

    **Request body:**
    - `content` (required, 1-1000 chars): New comment text
    """,
    responses={
        200: {
            "description": "Comment updated",
            "content": {
                "application/json": {"example": CommentExamples.UPDATE_SUCCESS}
            },
        },
        403: {"description": "Permission denied"},
    },
)
async def update_comment(
    comment_id: int,
    comment_in: CommentUpdate,
    current_user: UserModel = Depends(require_permissions_db("comment:update:own")),
    comment_service: CommentService = Depends(get_comment_service),
) -> CommentRead:
    """Update a comment."""
    return await comment_service.update_comment(
        comment_id=comment_id,
        content=comment_in.content,
        current_user=current_user,
    )


@router.delete(
    "/comments/{comment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete comment",
    description="""
    Delete a comment.

    **Permissions required:** COMMENT_AUTHOR or GROUP_ADMIN

    **Side effects:** Deletes all replies if parent is deleted.
    """,
    responses={
        204: {"description": "Comment deleted successfully"},
    },
)
async def delete_comment(
    comment_id: int,
    current_user: UserModel = Depends(require_permissions_db("comment:delete:own")),
    comment_service: CommentService = Depends(get_comment_service),
) -> None:
    """Delete a comment."""
    await comment_service.delete_comment(comment_id, current_user)
