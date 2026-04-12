from datetime import datetime
from typing import Any, Dict
import uuid

from pydantic import BaseModel, ConfigDict, Field

from ..models.enums import AuditAction


class AuditLogCreate(BaseModel):
    action: AuditAction
    entity_type: str
    entity_id: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AuditLogRead(AuditLogCreate):
    id: uuid.UUID
    user_id: uuid.UUID
    metadata: Dict[str, Any] = Field(default_factory=dict, alias="metadata_json")
    created_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
