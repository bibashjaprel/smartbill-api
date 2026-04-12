from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
import uuid


class ShopBase(BaseModel):
    name: str
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    subscription_plan: Optional[str] = "trial"
    subscription_status: Optional[str] = "active"
    billing_cycle: Optional[str] = "monthly"
    manual_billing_amount: Optional[Decimal] = Decimal('0.00')
    next_billing_date: Optional[datetime] = None
    subscription_started_at: Optional[datetime] = None
    subscription_ends_at: Optional[datetime] = None
    auto_renew: Optional[bool] = True


class ShopCreate(ShopBase):
    owner_id: Optional[uuid.UUID] = None  # Platform admins can specify owner


class ShopUpdate(ShopBase):
    name: Optional[str] = None


class ShopInDBBase(ShopBase):
    id: uuid.UUID
    owner_id: uuid.UUID
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Shop(ShopInDBBase):
    pass


class ShopWithDetails(ShopInDBBase):
    customers_count: Optional[int] = 0
    products_count: Optional[int] = 0
    total_bills: Optional[int] = 0
    total_revenue: Optional[Decimal] = Decimal('0.00')
