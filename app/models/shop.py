from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Numeric, Boolean
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
    subscription_plan = Column(String(50), nullable=False, default="trial")
    subscription_status = Column(String(30), nullable=False, default="active")
    billing_cycle = Column(String(20), nullable=False, default="monthly")
    manual_billing_amount = Column(Numeric(10, 2), nullable=False, default=0)
    next_billing_date = Column(DateTime, nullable=True)
    subscription_started_at = Column(DateTime, server_default=func.now())
    subscription_ends_at = Column(DateTime, nullable=True)
    auto_renew = Column(Boolean, nullable=False, default=True)
    owner_id = Column(GUID, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    owner = relationship("User", foreign_keys=[owner_id], back_populates="owned_shops")
    user_roles = relationship("UserShopRole", back_populates="shop", cascade="all, delete-orphan")
    customers = relationship("Customer", back_populates="shop", cascade="all, delete-orphan")
    products = relationship("Product", back_populates="shop", cascade="all, delete-orphan")
    bills = relationship("Bill", back_populates="shop", cascade="all, delete-orphan")
    stock_movements = relationship("StockMovement", back_populates="shop", cascade="all, delete-orphan")
