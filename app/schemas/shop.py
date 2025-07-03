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


class ShopCreate(ShopBase):
    pass


class ShopUpdate(ShopBase):
    name: Optional[str] = None


class ShopInDBBase(ShopBase):
    id: uuid.UUID
    owner_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class Shop(ShopInDBBase):
    pass


class ShopWithDetails(ShopInDBBase):
    customers_count: Optional[int] = 0
    products_count: Optional[int] = 0
    total_bills: Optional[int] = 0
    total_revenue: Optional[Decimal] = Decimal('0.00')
