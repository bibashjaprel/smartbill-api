from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from ..core.database import Base, GUID


class UserShopRole(Base):
    __tablename__ = "user_shop_roles"
    __table_args__ = (
        UniqueConstraint("user_id", "shop_id", name="uq_user_shop_roles_user_shop"),
    )

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID, ForeignKey("users.id"), nullable=False, index=True)
    shop_id = Column(GUID, ForeignKey("shops.id"), nullable=False, index=True)
    role = Column(String(50), nullable=False, default="employee")
    is_active = Column(Boolean, nullable=False, default=True)
    joined_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="shop_roles")
    shop = relationship("Shop", back_populates="user_roles")
