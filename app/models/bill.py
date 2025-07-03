from sqlalchemy import Column, String, DateTime, ForeignKey, Numeric, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from ..core.database import Base


class Bill(Base):
    __tablename__ = "bills"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    bill_number = Column(String(50), nullable=False)
    customer_id = Column(String(36), ForeignKey("customers.id"))
    shop_id = Column(String(36), ForeignKey("shops.id"), nullable=False)
    total_amount = Column(Numeric(10, 2), nullable=False)
    paid_amount = Column(Numeric(10, 2), default=0.00)
    payment_method = Column(String(50), default='cash')
    payment_status = Column(String(20), default='pending')
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    shop = relationship("Shop", back_populates="bills")
    customer = relationship("Customer", back_populates="bills")
    bill_items = relationship("BillItem", back_populates="bill", cascade="all, delete-orphan")
    udharo_transactions = relationship("UdharoTransaction", back_populates="bill")


class BillItem(Base):
    __tablename__ = "bill_items"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    bill_id = Column(String(36), ForeignKey("bills.id"), nullable=False)
    product_id = Column(String(36), ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    total_price = Column(Numeric(10, 2), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    bill = relationship("Bill", back_populates="bill_items")
    product = relationship("Product", back_populates="bill_items")


class UdharoTransaction(Base):
    __tablename__ = "udharo_transactions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    customer_id = Column(String(36), ForeignKey("customers.id"), nullable=False)
    bill_id = Column(String(36), ForeignKey("bills.id"))
    amount = Column(Numeric(10, 2), nullable=False)
    transaction_type = Column(String(20), nullable=False)  # 'credit' or 'payment'
    description = Column(String(500))
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    customer = relationship("Customer", back_populates="udharo_transactions")
    bill = relationship("Bill", back_populates="udharo_transactions")
