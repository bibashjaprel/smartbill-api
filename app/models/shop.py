from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from sqlalchemy.dialects.postgresql import UUID
from ..core.database import Base, GUID


class Shop(Base):
    __tablename__ = "shops"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    address = Column(Text)
    phone = Column(String(20))
    email = Column(String(255))
    owner_id = Column(GUID, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    owner = relationship("User", foreign_keys=[owner_id], back_populates="owned_shops")
    users = relationship("User", foreign_keys="User.shop_id", back_populates="current_shop")
    customers = relationship("Customer", back_populates="shop", cascade="all, delete-orphan")
    products = relationship("Product", back_populates="shop", cascade="all, delete-orphan")
    bills = relationship("Bill", back_populates="shop", cascade="all, delete-orphan")
