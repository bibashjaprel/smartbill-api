import uuid

from sqlalchemy import Column, DateTime, Enum, ForeignKey, String
from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..core.database import Base, GUID
from .enums import AuditAction

jsonb_type = JSON().with_variant(JSONB, "postgresql")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID, ForeignKey("users.id"), nullable=False, index=True)
    action = Column(Enum(AuditAction, name="audit_action_enum"), nullable=False)
    entity_type = Column(String(120), nullable=False, index=True)
    entity_id = Column(String(120), nullable=False, index=True)
    metadata_json = Column("metadata", jsonb_type, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    user = relationship("User", back_populates="audit_logs")
