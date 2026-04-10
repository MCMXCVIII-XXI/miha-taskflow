from fastapi import APIRouter, Depends, status

from app.core.permission import require_permissions_db
from app.models import User as UserModel
from app.schemas import CommentCreate, CommentRead, CommentUpdate
from app.service import CommentService, get_comment_service

router = APIRouter()


@router.post(
    "/tasks/{task_id}/comments",
    response_model=CommentRead,
    status_code=status.HTTP_201_CREATED,
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
)
async def get_task_comments(
    task_id: int,
    limit: int = 50,
    offset: int = 0,
    current_user: UserModel = Depends(require_permissions_db("comment:view:any")),
    comment_service: CommentService = Depends(get_comment_service),
) -> list[CommentRead]:
    """Get comments for a specific task with pagination."""
    return await comment_service.get_task_comments(task_id, limit, offset)


@router.get(
    "/comments/{comment_id}",
    response_model=CommentRead,
    status_code=status.HTTP_200_OK,
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
)
async def delete_comment(
    comment_id: int,
    current_user: UserModel = Depends(require_permissions_db("comment:delete:own")),
    comment_service: CommentService = Depends(get_comment_service),
) -> None:
    """Delete a comment."""
    await comment_service.delete_comment(comment_id, current_user)
