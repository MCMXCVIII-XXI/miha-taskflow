from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import StreamingResponse

from app.core.permission import require_permissions_db
from app.examples.notification_examples import NotificationExamples, SSEExamples
from app.models import User as UserModel
from app.schemas import NotificationRead, NotificationRespond
from app.schemas.enum import NotificationStatus, NotificationType
from app.service import (
    NotificationService,
    SSEService,
    get_notification_service,
    get_sse_service,
)

router = APIRouter(tags=["notifications"])


@router.get(
    "",
    response_model=list[NotificationRead],
    status_code=status.HTTP_200_OK,
    summary="Get notifications",
    description="""
    Get notifications for the current user.

    **Permissions required:** AUTHENTICATED_USER

    **Query parameters:**
    - `status` (optional): Filter by READ or UNREAD
    - `type` (optional): Filter by notification type
    - `limit` (default: 50, max: 100): Max notifications to return
    - `offset` (default: 0): Number of notifications to skip

    **Returns:** List of notifications sorted by created_at (newest first).
    """,
    responses={
        200: {
            "description": "Notifications retrieved",
            "content": {"application/json": {"example": NotificationExamples.GET_ALL}},
        },
    },
)
async def get_notifications(
    current_user: UserModel = Depends(require_permissions_db("notification:view:own")),
    status: NotificationStatus | None = None,
    type: NotificationType | None = None,
    limit: int = Query(50, le=100, description="Max notifications to return"),
    offset: int = Query(0, ge=0, description="Number of notifications to skip"),
    svc: NotificationService = Depends(get_notification_service),
) -> list[NotificationRead]:
    """Endpoint for retrieving notifications"""
    return await svc.get_notifications(
        user_id=current_user.id,
        status=status,
        type=type,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/stream",
    response_class=StreamingResponse,
    status_code=status.HTTP_200_OK,
    summary="Subscribe to notifications (SSE)",
    description="""
    Open a Server-Sent Events (SSE) stream for real-time notifications.

    **Permissions required:** AUTHENTICATED_USER

    **Returns:** Event stream with notification events.

    **Event types:**
    - `connected`: Initial connection confirmation
    - `notification`: New notification received

    **Headers:**
    - Cache-Control: no-cache
    - Connection: keep-alive
    """,
    responses={
        200: {
            "description": "SSE stream connected",
            "content": {"text/event-stream": {"example": SSEExamples.SSE_CONNECTED}},
        },
    },
)
async def notifications_stream(
    current_user: UserModel = Depends(require_permissions_db("notification:view:own")),
    svc: SSEService = Depends(get_sse_service),
) -> StreamingResponse:
    return StreamingResponse(
        svc.event_generator(current_user.id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get(
    "/unread-count",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Get unread count",
    description="""
    Get the count of unread notifications.

    **Permissions required:** AUTHENTICATED_USER

    **Returns:** Object with unread_count field.
    """,
    responses={
        200: {
            "description": "Unread count retrieved",
            "content": {
                "application/json": {"example": NotificationExamples.UNREAD_COUNT}
            },
        },
    },
)
async def get_unread_count(
    current_user: UserModel = Depends(require_permissions_db("notification:view:own")),
    service: NotificationService = Depends(get_notification_service),
) -> dict[str, int]:
    """Endpoint for retrieving the count of unread notifications"""
    notifications = await service.get_notifications(
        user_id=current_user.id,
        status=NotificationStatus.UNREAD,
    )
    return {"count": len(notifications)}


@router.get(
    "/{notification_id}",
    response_model=NotificationRead,
    status_code=status.HTTP_200_OK,
    summary="Get notification",
    description="""
    Get a notification by ID.

    **Permissions required:** AUTHENTICATED_USER (owner only)
    """,
    responses={
        200: {
            "description": "Notification retrieved",
        },
        404: {
            "description": "Notification not found",
            "content": {
                "application/json": {"example": NotificationExamples.NOT_FOUND}
            },
        },
    },
)
async def get_notification(
    notification_id: int,
    current_user: UserModel = Depends(require_permissions_db("notification:view:own")),
    service: NotificationService = Depends(get_notification_service),
) -> NotificationRead:
    """Endpoint for retrieving a notification by ID"""
    return await service.get_notification(notification_id, current_user.id)


@router.patch(
    "/{notification_id}/read",
    response_model=NotificationRead,
    status_code=status.HTTP_200_OK,
    summary="Mark as read",
    description="""
    Mark a notification as read.

    **Permissions required:** AUTHENTICATED_USER (owner only)
    """,
    responses={
        200: {
            "description": "Notification marked as read",
            "content": {
                "application/json": {"example": NotificationExamples.MARK_READ_SUCCESS}
            },
        },
    },
)
async def mark_notification_read(
    notification_id: int,
    current_user: UserModel = Depends(require_permissions_db("notification:view:own")),
    service: NotificationService = Depends(get_notification_service),
) -> NotificationRead:
    """Endpoint for marking a notification as read"""
    return await service.mark_as_read(notification_id, current_user.id)


@router.patch(
    "/read-all",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Mark all as read",
    description="""
    Mark all notifications as read.

    **Permissions required:** AUTHENTICATED_USER

    **Returns:** Object with updated_count field.
    """,
    responses={
        200: {
            "description": "All notifications marked as read",
            "content": {
                "application/json": {
                    "example": NotificationExamples.MARK_ALL_READ_SUCCESS
                }
            },
        },
    },
)
async def mark_all_notifications_read(
    current_user: UserModel = Depends(require_permissions_db("notification:view:own")),
    service: NotificationService = Depends(get_notification_service),
) -> dict[str, int]:
    """Endpoint for marking all notifications as read"""
    count = await service.mark_all_as_read(current_user.id)
    return {"updated_count": count}


@router.post(
    "/{notification_id}/respond",
    response_model=NotificationRead,
    status_code=status.HTTP_200_OK,
    summary="Respond to notification",
    description="""
    Respond to a notification (accept or reject).

    **Permissions required:** AUTHENTICATED_USER (owner only)

    **Request body:**
    - `response` (required): ACCEPT or REJECT

    **Used for:** TASK_INVITE, GROUP_INVITE notifications
    """,
    responses={
        200: {"description": "Response recorded"},
    },
)
async def respond_to_notification(
    notification_id: int,
    respond_in: NotificationRespond,
    current_user: UserModel = Depends(
        require_permissions_db("notification:respond:own")
    ),
    service: NotificationService = Depends(get_notification_service),
) -> NotificationRead:
    """Endpoint for responding to a notification (accept/reject)"""
    return await service.respond_to_notification(
        notification_id=notification_id,
        user_id=current_user.id,
        response=respond_in.response,
    )
