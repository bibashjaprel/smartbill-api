from sqlalchemy import Column, DateTime, Enum, ForeignKey, Boolean, UniqueConstraint
from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from ..core.database import Base, GUID
from .enums import ShopRole

jsonb_type = JSON().with_variant(JSONB, "postgresql")


class UserShopRole(Base):
    __tablename__ = "user_shop_roles"
    __table_args__ = (
        UniqueConstraint("user_id", "shop_id", name="uq_user_shop_roles_user_shop"),
    )

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID, ForeignKey("users.id"), nullable=False, index=True)
    shop_id = Column(GUID, ForeignKey("shops.id"), nullable=False, index=True)
    role = Column(Enum(ShopRole, name="shop_role_enum"), nullable=False, default=ShopRole.staff)
    permissions = Column(jsonb_type, nullable=False, default=dict)
    is_active = Column(Boolean, nullable=False, default=True)
    joined_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="shop_roles")
    shop = relationship("Shop", back_populates="user_roles")
