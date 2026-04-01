from fastapi import APIRouter, Depends, Query, status

from app.core.permission import require_permissions_db
from app.models import User as UserModel
from app.schemas import (
    NotificationRead,
    NotificationRespond,
    NotificationStatus,
    NotificationType,
)
from app.service import NotificationService, get_notification_service

router = APIRouter()


@router.get("", response_model=list[NotificationRead], status_code=status.HTTP_200_OK)
async def get_notifications(
    current_user: UserModel = Depends(require_permissions_db("notification:view:own")),
    status: NotificationStatus | None = None,
    type: NotificationType | None = None,
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    svc: NotificationService = Depends(get_notification_service),
) -> list[NotificationRead]:
    return await svc.get_notifications(
        user_id=current_user.id,
        status=status,
        type=type,
        limit=limit,
        offset=offset,
    )


@router.get("/unread-count", response_model=dict)
async def get_unread_count(
    current_user: UserModel = Depends(require_permissions_db("notification:view:own")),
    service: NotificationService = Depends(get_notification_service),
) -> dict[str, int]:
    notifications = await service.get_notifications(
        user_id=current_user.id,
        status=NotificationStatus.UNREAD,
    )
    return {"count": len(notifications)}


@router.get("/{notification_id}", response_model=NotificationRead)
async def get_notification(
    notification_id: int,
    current_user: UserModel = Depends(require_permissions_db("notification:view:own")),
    service: NotificationService = Depends(get_notification_service),
) -> NotificationRead:
    return await service.get_notification(notification_id, current_user.id)


@router.patch("/{notification_id}/read", response_model=NotificationRead)
async def mark_notification_read(
    notification_id: int,
    current_user: UserModel = Depends(require_permissions_db("notification:view:own")),
    service: NotificationService = Depends(get_notification_service),
) -> NotificationRead:
    return await service.mark_as_read(notification_id, current_user.id)


@router.patch("/read-all", response_model=dict)
async def mark_all_notifications_read(
    current_user: UserModel = Depends(require_permissions_db("notification:view:own")),
    service: NotificationService = Depends(get_notification_service),
) -> dict[str, int]:
    """Пометить все уведомления прочитанными"""
    count = await service.mark_all_as_read(current_user.id)
    return {"updated_count": count}


@router.post("/{notification_id}/respond", response_model=NotificationRead)
async def respond_to_notification(
    notification_id: int,
    respond_in: NotificationRespond,
    current_user: UserModel = Depends(
        require_permissions_db("notification:respond:own")
    ),
    service: NotificationService = Depends(get_notification_service),
) -> NotificationRead:
    """Ответить на уведомление (принять/отклонить)"""
    return await service.respond_to_notification(
        notification_id=notification_id,
        user_id=current_user.id,
        response=respond_in.response,
    )
