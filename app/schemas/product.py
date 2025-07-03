from pydantic import BaseModel, Field
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
    cost_price: Optional[Decimal] = None
    min_stock_level: Optional[int] = 0
    sku: Optional[str] = None


class ProductCreate(ProductBase):
    shop_id: Optional[uuid.UUID] = None


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
    current_stock: Optional[int] = None
    
    class Config:
        orm_mode = True
        
    @classmethod
    def from_orm(cls, obj):
        # Create the product instance
        product = super().from_orm(obj)
        # Set current_stock to the same value as stock_quantity
        product.current_stock = product.stock_quantity
        return product


class ProductWithStats(ProductInDBBase):
    total_sold: Optional[int] = 0
    total_revenue: Optional[Decimal] = Decimal('0.00')
    last_sold_date: Optional[datetime] = None
