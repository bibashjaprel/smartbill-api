from typing import List
from uuid import UUID

from sqlalchemy.orm import Session

from ..models.audit_log import AuditLog
from ..schemas.audit import AuditLogCreate
from .base import CRUDBase


class CRUDAuditLog(CRUDBase[AuditLog, AuditLogCreate, dict]):
    def get_recent(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[AuditLog]:
        return db.query(AuditLog).order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()

    def get_by_user(self, db: Session, *, user_id: UUID, skip: int = 0, limit: int = 100) -> List[AuditLog]:
        return (
            db.query(AuditLog)
            .filter(AuditLog.user_id == user_id)
            .order_by(AuditLog.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )


audit_log = CRUDAuditLog(AuditLog)
