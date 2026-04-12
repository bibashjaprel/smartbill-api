from typing import List
from uuid import UUID

from sqlalchemy.orm import Session

from ..models.notification import Notification
from ..schemas.notification import NotificationCreate
from .base import CRUDBase


class CRUDNotification(CRUDBase[Notification, NotificationCreate, dict]):
    def get_by_user(self, db: Session, *, user_id: UUID, skip: int = 0, limit: int = 100) -> List[Notification]:
        return (
            db.query(Notification)
            .filter(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )


notification = CRUDNotification(Notification)
