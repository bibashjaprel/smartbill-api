import uuid

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Index, Numeric, String
from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..core.database import Base, GUID
from .enums import BillingCycle, PaymentProvider, PaymentStatus, SubscriptionStatus

jsonb_type = JSON().with_variant(JSONB, "postgresql")


class Plan(Base):
    __tablename__ = "plans"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    name = Column(String(120), nullable=False, unique=True)
    price = Column(Numeric(12, 2), nullable=False)
    billing_cycle = Column(Enum(BillingCycle, name="billing_cycle_enum"), nullable=False)
    features = Column(jsonb_type, nullable=False, default=dict)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    subscriptions = relationship("Subscription", back_populates="plan")


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    shop_id = Column(GUID, ForeignKey("shops.id"), nullable=False, index=True)
    plan_id = Column(GUID, ForeignKey("plans.id"), nullable=False, index=True)
    status = Column(Enum(SubscriptionStatus, name="subscription_status_enum"), nullable=False, default=SubscriptionStatus.trial)
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=True)
    trial_end = Column(DateTime(timezone=True), nullable=True)
    current_period_start = Column(DateTime(timezone=True), nullable=False)
    current_period_end = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    shop = relationship("Shop", back_populates="subscriptions")
    plan = relationship("Plan", back_populates="subscriptions")
    payments = relationship("Payment", back_populates="subscription", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_subscriptions_shop_status", "shop_id", "status"),
    )


class Payment(Base):
    __tablename__ = "payments"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    subscription_id = Column(GUID, ForeignKey("subscriptions.id"), nullable=False, index=True)
    amount = Column(Numeric(12, 2), nullable=False)
    status = Column(Enum(PaymentStatus, name="payment_status_enum"), nullable=False, default=PaymentStatus.pending)
    provider = Column(Enum(PaymentProvider, name="payment_provider_enum"), nullable=False)
    transaction_ref = Column(String(255), nullable=True, index=True)
    paid_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    subscription = relationship("Subscription", back_populates="payments")
