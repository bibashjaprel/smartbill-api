from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ...api.deps import get_current_active_user
from ...core.database import get_db
from ...models.audit_log import AuditLog
from ...models.user import User
from ...schemas.audit import AuditLogRead

router = APIRouter()


@router.get("/audit/logs", response_model=List[AuditLogRead])
def list_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    if current_user.role not in ["super_admin", "platform_admin"]:
        return []

    return (
        db.query(AuditLog)
        .order_by(AuditLog.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
