from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from sqlalchemy.dialects.postgresql import UUID
from ..core.database import Base, GUID


class Customer(Base):
    __tablename__ = "customers"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    phone = Column(String(20))
    email = Column(String(255))
    address = Column(Text)
    udharo_balance = Column(Numeric(10, 2), default=0.00)
    shop_id = Column(GUID, ForeignKey("shops.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    shop = relationship("Shop", back_populates="customers")
    invoices = relationship("Invoice", back_populates="customer")
