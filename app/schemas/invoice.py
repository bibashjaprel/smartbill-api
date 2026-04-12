from datetime import datetime
from decimal import Decimal
from typing import List, Optional
import uuid

from pydantic import BaseModel, ConfigDict, Field

from ..models.enums import InvoiceStatus


class InvoiceItemCreate(BaseModel):
    product_id: uuid.UUID
    quantity: int = Field(..., gt=0)
    price: Decimal = Field(..., ge=0)


class InvoiceItemRead(InvoiceItemCreate):
    id: uuid.UUID
    invoice_id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InvoiceCreate(BaseModel):
    customer_id: uuid.UUID
    due_date: Optional[datetime] = None
    items: List[InvoiceItemCreate]


class InvoiceRead(BaseModel):
    id: uuid.UUID
    shop_id: uuid.UUID
    customer_id: uuid.UUID
    total_amount: Decimal
    paid_amount: Decimal
    status: InvoiceStatus
    due_date: Optional[datetime]
    created_at: datetime
    items: List[InvoiceItemRead] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class InvoicePaymentCreate(BaseModel):
    amount: Decimal = Field(..., gt=0)
    method: str
    paid_at: datetime


class InvoicePaymentRead(InvoicePaymentCreate):
    id: uuid.UUID
    invoice_id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
