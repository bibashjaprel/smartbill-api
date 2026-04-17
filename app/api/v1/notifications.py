from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from ...api.deps import get_current_active_user
from ...core.database import get_db
from ...core.transaction import write_transaction
from ...models.notification import Notification
from ...models.user import User
from ...modules.notifications.service import NotificationService
from ...schemas.notification import NotificationCreate, NotificationRead
from ...utils.api_response import paginated_response, success_response

router = APIRouter()


@router.get("/notifications")
def list_my_notifications(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    query = (
        db.query(Notification)
        .filter(Notification.user_id == current_user.id)
        .order_by(Notification.created_at.desc())
    )
    total = query.count()
    rows = query.offset(skip).limit(limit).all()
    return paginated_response(
        [NotificationRead.model_validate(row).model_dump(mode="json") for row in rows],
        total=total,
        limit=limit,
        skip=skip,
        request_id=getattr(request.state, "request_id", None),
    )


@router.post("/notifications")
def create_notification(
    payload: NotificationCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    if payload.user_id != current_user.id and current_user.role not in ["platform_admin", "super_admin"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot create notification for another user")
    with write_transaction(db):
        row = NotificationService.create(db, payload)
    return success_response(
        NotificationRead.model_validate(row).model_dump(mode="json"),
        request_id=getattr(request.state, "request_id", None),
    )


@router.post("/notifications/{notification_id}/read")
def mark_notification_read(
    notification_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    notification = (
        db.query(Notification)
        .filter(Notification.id == notification_id, Notification.user_id == current_user.id)
        .first()
    )
    if not notification:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    with write_transaction(db):
        row = NotificationService.mark_read(db, notification)
    return success_response(
        NotificationRead.model_validate(row).model_dump(mode="json"),
        request_id=getattr(request.state, "request_id", None),
    )
