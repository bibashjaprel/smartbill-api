from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from .invoice import InvoicePaymentRead


class CustomerCreditSummary(BaseModel):
    customer_id: UUID
    total_invoiced: Decimal
    total_paid: Decimal
    total_due: Decimal
    outstanding_invoice_count: int


class CreditPaymentCreate(BaseModel):
    invoice_id: UUID
    amount: Decimal = Field(..., gt=0)
    method: str
    paid_at: Optional[datetime] = None


class CreditInvoiceItem(BaseModel):
    invoice_id: UUID
    total_amount: Decimal
    paid_amount: Decimal
    due_amount: Decimal
    due_date: Optional[datetime] = None


class CreditLedgerRead(BaseModel):
    customer_id: UUID
    invoices: List[CreditInvoiceItem]
    recent_payments: List[InvoicePaymentRead] = Field(default_factory=list)
