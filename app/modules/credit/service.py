from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from ...models.enums import InvoiceStatus
from ...models.invoice import Invoice, InvoicePayment
from ...modules.billing.service import BillingService
from ...schemas.credit import CreditLedgerRead, CreditPaymentCreate, CustomerCreditSummary
from ...schemas.invoice import InvoicePaymentCreate


class CreditService:
    @staticmethod
    def get_customer_summary(db: Session, shop_id: UUID, customer_id: UUID) -> CustomerCreditSummary:
        totals = (
            db.query(
                func.coalesce(func.sum(Invoice.total_amount), 0),
                func.coalesce(func.sum(Invoice.paid_amount), 0),
                func.count(Invoice.id),
            )
            .filter(Invoice.shop_id == shop_id, Invoice.customer_id == customer_id)
            .one()
        )

        total_invoiced = Decimal(totals[0])
        total_paid = Decimal(totals[1])
        total_due = total_invoiced - total_paid

        outstanding_count = (
            db.query(func.count(Invoice.id))
            .filter(
                Invoice.shop_id == shop_id,
                Invoice.customer_id == customer_id,
                Invoice.status.in_([InvoiceStatus.unpaid, InvoiceStatus.partial]),
            )
            .scalar()
            or 0
        )

        return CustomerCreditSummary(
            customer_id=customer_id,
            total_invoiced=total_invoiced,
            total_paid=total_paid,
            total_due=total_due,
            outstanding_invoice_count=int(outstanding_count),
        )

    @staticmethod
    def get_customer_ledger(db: Session, shop_id: UUID, customer_id: UUID) -> CreditLedgerRead:
        invoices = (
            db.query(Invoice)
            .filter(
                Invoice.shop_id == shop_id,
                Invoice.customer_id == customer_id,
                Invoice.status.in_([InvoiceStatus.unpaid, InvoiceStatus.partial]),
            )
            .order_by(Invoice.created_at.desc())
            .all()
        )

        invoice_ids = [item.id for item in invoices]
        recent_payments = []
        if invoice_ids:
            recent_payments = (
                db.query(InvoicePayment)
                .filter(InvoicePayment.invoice_id.in_(invoice_ids))
                .order_by(InvoicePayment.paid_at.desc())
                .limit(50)
                .all()
            )

        return CreditLedgerRead(
            customer_id=customer_id,
            invoices=[
                {
                    "invoice_id": invoice.id,
                    "total_amount": invoice.total_amount,
                    "paid_amount": invoice.paid_amount,
                    "due_amount": Decimal(invoice.total_amount) - Decimal(invoice.paid_amount),
                    "due_date": invoice.due_date,
                }
                for invoice in invoices
            ],
            recent_payments=recent_payments,
        )

    @staticmethod
    def apply_payment(db: Session, shop_id: UUID, customer_id: UUID, payload: CreditPaymentCreate) -> Invoice:
        invoice = (
            db.query(Invoice)
            .filter(
                Invoice.id == payload.invoice_id,
                Invoice.shop_id == shop_id,
                Invoice.customer_id == customer_id,
            )
            .first()
        )
        if not invoice:
            raise ValueError("Invoice not found for customer")

        return BillingService.add_payment(
            db,
            invoice,
            InvoicePaymentCreate(
                amount=payload.amount,
                method=payload.method,
                paid_at=payload.paid_at or datetime.now(timezone.utc),
            ),
        )
