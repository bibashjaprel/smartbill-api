from uuid import UUID

from sqlalchemy.orm import Session

from ...models.audit_log import AuditLog
from ...schemas.audit import AuditLogCreate


class AuditService:
    @staticmethod
    def log(db: Session, user_id: UUID, payload: AuditLogCreate) -> AuditLog:
        log = AuditLog(
            user_id=user_id,
            action=payload.action,
            entity_type=payload.entity_type,
            entity_id=payload.entity_id,
            metadata_json=payload.metadata,
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return log
