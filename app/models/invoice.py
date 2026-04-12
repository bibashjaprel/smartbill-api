import uuid

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Index, Integer, Numeric, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..core.database import Base, GUID
from .enums import InvoiceStatus


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    shop_id = Column(GUID, ForeignKey("shops.id"), nullable=False, index=True)
    customer_id = Column(GUID, ForeignKey("customers.id"), nullable=False, index=True)
    total_amount = Column(Numeric(12, 2), nullable=False)
    paid_amount = Column(Numeric(12, 2), nullable=False, default=0)
    status = Column(Enum(InvoiceStatus, name="invoice_status_enum"), nullable=False, default=InvoiceStatus.unpaid)
    due_date = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    shop = relationship("Shop", back_populates="invoices")
    customer = relationship("Customer", back_populates="invoices")
    items = relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan")
    payments = relationship("InvoicePayment", back_populates="invoice", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_invoices_shop_status", "shop_id", "status"),
    )


class InvoiceItem(Base):
    __tablename__ = "invoice_items"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    invoice_id = Column(GUID, ForeignKey("invoices.id"), nullable=False, index=True)
    product_id = Column(GUID, ForeignKey("products.id"), nullable=False, index=True)
    quantity = Column(Integer, nullable=False)
    price = Column(Numeric(12, 2), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    invoice = relationship("Invoice", back_populates="items")
    product = relationship("Product", back_populates="invoice_items")


class InvoicePayment(Base):
    __tablename__ = "invoice_payments"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    invoice_id = Column(GUID, ForeignKey("invoices.id"), nullable=False, index=True)
    amount = Column(Numeric(12, 2), nullable=False)
    method = Column(String(50), nullable=False)
    paid_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    invoice = relationship("Invoice", back_populates="payments")
