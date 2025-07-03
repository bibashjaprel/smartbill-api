from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from decimal import Decimal
import uuid


class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: Decimal
    stock_quantity: Optional[int] = 0
    unit: Optional[str] = 'piece'
    category: Optional[str] = None


class ProductCreate(ProductBase):
    shop_id: uuid.UUID


class ProductUpdate(ProductBase):
    name: Optional[str] = None
    price: Optional[Decimal] = None


class ProductInDBBase(ProductBase):
    id: uuid.UUID
    shop_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class Product(ProductInDBBase):
    pass


class ProductWithStats(ProductInDBBase):
    total_sold: Optional[int] = 0
    total_revenue: Optional[Decimal] = Decimal('0.00')
    last_sold_date: Optional[datetime] = None
