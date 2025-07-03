from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from ..core.database import Base


class Customer(Base):
    __tablename__ = "customers"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    phone = Column(String(20))
    email = Column(String(255))
    address = Column(Text)
    udharo_balance = Column(Numeric(10, 2), default=0.00)
    shop_id = Column(String(36), ForeignKey("shops.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    shop = relationship("Shop", back_populates="customers")
    bills = relationship("Bill", back_populates="customer")
    udharo_transactions = relationship("UdharoTransaction", back_populates="customer", cascade="all, delete-orphan")
