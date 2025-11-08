from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from sqlalchemy.dialects.postgresql import UUID
from ..core.database import Base, GUID


class User(Base):
    __tablename__ = "users"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=True)  # Nullable for Google OAuth users
    full_name = Column(String(255))
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    role = Column(String(50), default="employee")  # super_admin, platform_admin, shop_owner, admin, manager, employee
    shop_id = Column(GUID, ForeignKey("shops.id"), nullable=True)  # Current/primary shop
    google_id = Column(String(255), unique=True, nullable=True, index=True)
    profile_picture = Column(String(500), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    current_shop = relationship("Shop", foreign_keys=[shop_id], back_populates="users")
    owned_shops = relationship("Shop", foreign_keys="Shop.owner_id", back_populates="owner", cascade="all, delete-orphan")
