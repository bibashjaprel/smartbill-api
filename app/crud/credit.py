from decimal import Decimal
from typing import List
from uuid import UUID

from sqlalchemy.orm import Session

from ..crud.invoice import invoice as crud_invoice
from ..models.enums import InvoiceStatus
from ..models.invoice import Invoice


class CRUDCredit:
    def get_outstanding_invoices(self, db: Session, *, shop_id: UUID, customer_id: UUID) -> List[Invoice]:
        invoices = crud_invoice.get_by_shop_and_customer(db, shop_id=shop_id, customer_id=customer_id)
        return [item for item in invoices if item.status in [InvoiceStatus.unpaid, InvoiceStatus.partial]]

    def get_outstanding_amount(self, db: Session, *, shop_id: UUID, customer_id: UUID) -> Decimal:
        invoices = self.get_outstanding_invoices(db, shop_id=shop_id, customer_id=customer_id)
        total_due = Decimal("0")
        for invoice in invoices:
            total_due += Decimal(invoice.total_amount) - Decimal(invoice.paid_amount)
        return total_due


credit = CRUDCredit()
