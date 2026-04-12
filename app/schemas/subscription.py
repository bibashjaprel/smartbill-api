from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Optional
import uuid

from pydantic import BaseModel, ConfigDict, Field

from ..models.enums import BillingCycle, PaymentProvider, PaymentStatus, SubscriptionStatus


class PlanBase(BaseModel):
    name: str
    price: Decimal
    billing_cycle: BillingCycle
    features: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True


class PlanCreate(PlanBase):
    pass


class PlanRead(PlanBase):
    id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SubscriptionBase(BaseModel):
    plan_id: uuid.UUID
    status: SubscriptionStatus = SubscriptionStatus.trial
    start_date: datetime
    end_date: Optional[datetime] = None
    trial_end: Optional[datetime] = None
    current_period_start: datetime
    current_period_end: datetime


class SubscriptionCreate(SubscriptionBase):
    pass


class SubscriptionRead(SubscriptionBase):
    id: uuid.UUID
    shop_id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SubscriptionPaymentCreate(BaseModel):
    amount: Decimal
    provider: PaymentProvider
    transaction_ref: Optional[str] = None
    status: PaymentStatus = PaymentStatus.pending
    paid_at: Optional[datetime] = None


class SubscriptionPaymentRead(BaseModel):
    id: uuid.UUID
    subscription_id: uuid.UUID
    amount: Decimal
    status: PaymentStatus
    provider: PaymentProvider
    transaction_ref: Optional[str]
    paid_at: Optional[datetime]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FeatureAccessRead(BaseModel):
    shop_id: uuid.UUID
    is_allowed: bool
    reason: Optional[str] = None
    limit: Optional[int] = None
    used: Optional[int] = None
