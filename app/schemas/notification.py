from datetime import datetime
import uuid

from pydantic import BaseModel, ConfigDict

from ..models.enums import NotificationType


class NotificationCreate(BaseModel):
    user_id: uuid.UUID
    type: NotificationType
    message: str


class NotificationRead(NotificationCreate):
    id: uuid.UUID
    is_read: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
