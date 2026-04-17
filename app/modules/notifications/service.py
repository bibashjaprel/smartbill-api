from sqlalchemy.orm import Session

from ...models.notification import Notification
from ...schemas.notification import NotificationCreate


class NotificationService:
    @staticmethod
    def create(db: Session, payload: NotificationCreate) -> Notification:
        notification = Notification(
            user_id=payload.user_id,
            type=payload.type,
            message=payload.message,
        )
        db.add(notification)
        db.flush()
        db.refresh(notification)
        return notification

    @staticmethod
    def mark_read(db: Session, notification: Notification) -> Notification:
        notification.is_read = True
        db.flush()
        db.refresh(notification)
        return notification
