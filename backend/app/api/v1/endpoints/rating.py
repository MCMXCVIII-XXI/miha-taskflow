from fastapi import APIRouter, Depends, status

from app.core.permission import require_permissions_db
from app.models import User as UserModel
from app.schemas import RatingCreate, RatingRead, RatingStats
from app.schemas.enum import RatingTarget
from app.service import RatingService, get_rating_service

router = APIRouter(tags=["ratings"])


@router.post(
    "/tasks/{task_id}/ratings",
    response_model=RatingRead,
    status_code=status.HTTP_201_CREATED,
    summary="Rate task",
    description="""
    Rate a completed task.

    **Permissions required:** GROUP_MEMBER (who was not assignee)

    **Request body:**
    - `score` (required, 1-5): Rating score

    **Constraints:**
    - Task must be completed (status = DONE)
    - User cannot rate their own task
    - One rating per user per task
    """,
    responses={
        201: {
            "description": "Rating created",
        },
        400: {"description": "Already rated or invalid state"},
        404: {"description": "Task not found"},
    },
)
async def create_task_rating(
    task_id: int,
    rating_in: RatingCreate,
    current_user: UserModel = Depends(require_permissions_db("rating:create:own")),
    rating_service: RatingService = Depends(get_rating_service),
) -> RatingRead:
    """Rate a completed task."""
    return await rating_service.create_rating(
        target_id=task_id,
        target_type=RatingTarget.TASK,
        score=rating_in.score,
        current_user=current_user,
    )


@router.get(
    "/tasks/{task_id}/ratings",
    response_model=RatingStats,
    status_code=status.HTTP_200_OK,
    summary="Get task ratings",
    description="""
    Get rating statistics for a task.

    **Permissions required:** GROUP_MEMBER

    **Returns:** Average score, count, and user's rating if exists.
    """,
    responses={
        200: {
            "description": "Rating stats retrieved",
        },
    },
)
async def get_task_rating(
    task_id: int,
    current_user: UserModel = Depends(require_permissions_db("rating:view:any")),
    rating_service: RatingService = Depends(get_rating_service),
) -> RatingStats:
    """Get task rating stats."""
    return await rating_service.get_task_rating(task_id)


@router.post(
    "/groups/{group_id}/ratings",
    response_model=RatingRead,
    status_code=status.HTTP_201_CREATED,
    summary="Rate group",
    description="""
    Rate a group.

    **Permissions required:** GROUP_MEMBER

    **Request body:**
    - `score` (required, 1-5): Rating score

    **Constraints:**
    - User must be group member
    - One rating per user per group
    """,
    responses={
        201: {
            "description": "Rating created",
        },
        400: {"description": "Already rated"},
    },
)
async def create_group_rating(
    group_id: int,
    rating_in: RatingCreate,
    current_user: UserModel = Depends(require_permissions_db("rating:create:own")),
    rating_service: RatingService = Depends(get_rating_service),
) -> RatingRead:
    """Rate a group."""
    return await rating_service.create_rating(
        target_id=group_id,
        target_type=RatingTarget.GROUP,
        score=rating_in.score,
        current_user=current_user,
    )


@router.get(
    "/groups/{group_id}/ratings",
    response_model=RatingStats,
    status_code=status.HTTP_200_OK,
    summary="Get group ratings",
    description="""
    Get rating statistics for a group.

    **Permissions required:** GROUP_MEMBER

    **Returns:** Average score, count, and user's rating if exists.
    """,
    responses={
        200: {
            "description": "Rating stats retrieved",
        },
    },
)
async def get_group_rating(
    group_id: int,
    current_user: UserModel = Depends(require_permissions_db("rating:view:any")),
    rating_service: RatingService = Depends(get_rating_service),
) -> RatingStats:
    """Get group rating stats."""
    return await rating_service.get_group_rating(group_id)


@router.delete(
    "/ratings/{rating_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete rating",
    description="""
    Delete own rating.

    **Permissions required:** RATING_AUTHOR only
    """,
    responses={
        204: {"description": "Rating deleted"},
    },
)
async def delete_rating(
    rating_id: int,
    current_user: UserModel = Depends(require_permissions_db("rating:delete:own")),
    rating_service: RatingService = Depends(get_rating_service),
) -> None:
    """Delete own rating."""
    await rating_service.delete_rating(rating_id, current_user)
