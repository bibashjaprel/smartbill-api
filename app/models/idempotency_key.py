import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from ..core.database import Base, GUID

jsonb_type = JSON().with_variant(JSONB, "postgresql")


class IdempotencyKey(Base):
    __tablename__ = "idempotency_keys"
    __table_args__ = (
        UniqueConstraint("key", "endpoint", "user_id", "shop_id", name="uq_idempotency_scope"),
    )

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    key = Column(String(128), nullable=False, index=True)
    endpoint = Column(String(120), nullable=False, index=True)
    user_id = Column(GUID, ForeignKey("users.id"), nullable=False, index=True)
    shop_id = Column(GUID, ForeignKey("shops.id"), nullable=False, index=True)
    request_hash = Column(String(64), nullable=False)
    status_code = Column(Integer, nullable=False, default=200)
    response_body = Column(jsonb_type, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
