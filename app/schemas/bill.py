from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
import uuid


class BillItemBase(BaseModel):
    product_id: uuid.UUID
    quantity: int
    unit_price: Decimal
    total_price: Decimal


class BillItemCreate(BillItemBase):
    pass


class BillItemInDBBase(BillItemBase):
    id: uuid.UUID
    bill_id: uuid.UUID
    created_at: datetime

    class Config:
        orm_mode = True


class BillItem(BillItemInDBBase):
    pass


class BillItemWithProduct(BillItemInDBBase):
    product_name: str
    product_unit: str


class BillBase(BaseModel):
    bill_number: str
    customer_id: Optional[uuid.UUID] = None
    total_amount: Decimal
    paid_amount: Optional[Decimal] = Decimal('0.00')
    payment_method: Optional[str] = 'cash'
    payment_status: Optional[str] = 'pending'


class BillCreate(BillBase):
    shop_id: uuid.UUID
    items: List[BillItemCreate]


class BillUpdate(BaseModel):
    paid_amount: Optional[Decimal] = None
    payment_method: Optional[str] = None
    payment_status: Optional[str] = None


class BillInDBBase(BillBase):
    id: uuid.UUID
    shop_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class Bill(BillInDBBase):
    pass


class BillWithDetails(BillInDBBase):
    items: List[BillItemWithProduct] = []
    customer_name: Optional[str] = None
    remaining_amount: Optional[Decimal] = Decimal('0.00')


class UdharoTransactionBase(BaseModel):
    amount: Decimal
    transaction_type: str  # 'credit' or 'payment'
    description: Optional[str] = None


class UdharoTransactionCreate(UdharoTransactionBase):
    customer_id: uuid.UUID
    bill_id: Optional[uuid.UUID] = None


class UdharoTransactionInDBBase(UdharoTransactionBase):
    id: uuid.UUID
    customer_id: uuid.UUID
    bill_id: Optional[uuid.UUID] = None
    created_at: datetime

    class Config:
        orm_mode = True


class UdharoTransaction(UdharoTransactionInDBBase):
    pass


class UdharoTransactionWithDetails(UdharoTransactionInDBBase):
    customer_name: str
    bill_number: Optional[str] = None
