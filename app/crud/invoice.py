from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session, selectinload

from ..models.invoice import Invoice, InvoicePayment
from ..schemas.invoice import InvoiceCreate
from .base import CRUDBase


class CRUDInvoice(CRUDBase[Invoice, InvoiceCreate, dict]):
    def get_by_shop(self, db: Session, *, shop_id: UUID, skip: int = 0, limit: int = 100) -> List[Invoice]:
        return (
            db.query(Invoice)
            .filter(Invoice.shop_id == shop_id)
            .options(selectinload(Invoice.items), selectinload(Invoice.payments))
            .order_by(Invoice.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_shop_and_id(self, db: Session, *, shop_id: UUID, invoice_id: UUID) -> Optional[Invoice]:
        return (
            db.query(Invoice)
            .filter(Invoice.shop_id == shop_id, Invoice.id == invoice_id)
            .options(selectinload(Invoice.items), selectinload(Invoice.payments))
            .first()
        )

    def get_by_shop_and_customer(self, db: Session, *, shop_id: UUID, customer_id: UUID) -> List[Invoice]:
        return (
            db.query(Invoice)
            .filter(Invoice.shop_id == shop_id, Invoice.customer_id == customer_id)
            .options(selectinload(Invoice.items), selectinload(Invoice.payments))
            .order_by(Invoice.created_at.desc())
            .all()
        )


class CRUDInvoicePayment(CRUDBase[InvoicePayment, dict, dict]):
    def get_by_invoice(self, db: Session, *, invoice_id: UUID) -> List[InvoicePayment]:
        return (
            db.query(InvoicePayment)
            .filter(InvoicePayment.invoice_id == invoice_id)
            .order_by(InvoicePayment.paid_at.desc())
            .all()
        )


invoice = CRUDInvoice(Invoice)
invoice_payment = CRUDInvoicePayment(InvoicePayment)
