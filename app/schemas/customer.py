from pydantic import BaseModel, ConfigDict, EmailStr
from typing import Optional
from datetime import datetime
from decimal import Decimal
import uuid


class CustomerBase(BaseModel):
    name: str
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None


class CustomerCreate(CustomerBase):
    shop_id: uuid.UUID


class CustomerUpdate(CustomerBase):
    name: Optional[str] = None


class CustomerInDBBase(CustomerBase):
    id: uuid.UUID
    udharo_balance: Decimal
    shop_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Customer(CustomerInDBBase):
    pass


class CustomerWithDetails(CustomerInDBBase):
    total_bills: Optional[int] = 0
    total_amount: Optional[Decimal] = Decimal('0.00')
    last_transaction_date: Optional[datetime] = None
