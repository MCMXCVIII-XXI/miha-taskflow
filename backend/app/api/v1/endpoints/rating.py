from fastapi import APIRouter, Depends, status

from app.core.permission import require_permissions_db
from app.models import User as UserModel
from app.schemas import RatingCreate, RatingRead, RatingStats
from app.schemas.enum import RatingTarget
from app.service import RatingService, get_rating_service

router = APIRouter()


@router.post(
    "/tasks/{task_id}/ratings",
    response_model=RatingRead,
    status_code=status.HTTP_201_CREATED,
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
)
async def delete_rating(
    rating_id: int,
    current_user: UserModel = Depends(require_permissions_db("rating:delete:own")),
    rating_service: RatingService = Depends(get_rating_service),
) -> None:
    """Delete own rating."""
    await rating_service.delete_rating(rating_id, current_user)
