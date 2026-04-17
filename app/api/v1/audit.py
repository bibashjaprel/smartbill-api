from typing import List

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from ...api.deps import get_current_active_user
from ...core.database import get_db
from ...models.audit_log import AuditLog
from ...models.user import User
from ...schemas.audit import AuditLogRead
from ...utils.api_response import paginated_response

router = APIRouter()


@router.get("/audit/logs")
def list_audit_logs(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    if current_user.role not in ["super_admin", "platform_admin"]:
        return paginated_response([], total=0, limit=limit, skip=skip, request_id=getattr(request.state, "request_id", None))

    query = (
        db.query(AuditLog)
        .order_by(AuditLog.created_at.desc())
    )
    total = query.count()
    rows = query.offset(skip).limit(limit).all()
    return paginated_response(
        [AuditLogRead.model_validate(row).model_dump(mode="json") for row in rows],
        total=total,
        limit=limit,
        skip=skip,
        request_id=getattr(request.state, "request_id", None),
    )
