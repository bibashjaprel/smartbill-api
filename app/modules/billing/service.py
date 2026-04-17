from decimal import Decimal
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

from ...models.invoice import Invoice, InvoiceItem, InvoicePayment
from ...models.product import Product
from ...models.enums import InvoiceStatus
from ...schemas.invoice import InvoiceCreate, InvoicePaymentCreate


class BillingService:
    @staticmethod
    def create_invoice(db: Session, shop_id: UUID, payload: InvoiceCreate) -> Invoice:
        total_amount = Decimal("0")
        invoice = Invoice(
            shop_id=shop_id,
            customer_id=payload.customer_id,
            due_date=payload.due_date,
            paid_amount=Decimal("0"),
            total_amount=Decimal("0"),
            status=InvoiceStatus.unpaid,
        )
        db.add(invoice)
        db.flush()

        for item in payload.items:
            product = db.query(Product).filter(Product.id == item.product_id, Product.shop_id == shop_id).first()
            if not product:
                raise ValueError(f"Product {item.product_id} not found for shop")

            line_total = Decimal(item.quantity) * Decimal(item.price)
            total_amount += line_total
            db.add(
                InvoiceItem(
                    invoice_id=invoice.id,
                    product_id=item.product_id,
                    quantity=item.quantity,
                    price=item.price,
                )
            )

        invoice.total_amount = total_amount
        BillingService._sync_invoice_status(db, invoice)
        db.flush()
        db.refresh(invoice)
        return invoice

    @staticmethod
    def add_payment(db: Session, invoice: Invoice, payload: InvoicePaymentCreate) -> Invoice:
        locked_invoice = (
            db.query(Invoice)
            .filter(Invoice.id == invoice.id)
            .with_for_update()
            .one()
        )

        current_paid_total = (
            db.query(func.coalesce(func.sum(InvoicePayment.amount), 0))
            .filter(InvoicePayment.invoice_id == locked_invoice.id)
            .scalar()
        )
        next_paid_total = Decimal(current_paid_total) + Decimal(payload.amount)
        if next_paid_total > Decimal(locked_invoice.total_amount):
            raise ValueError("Payment exceeds remaining invoice balance")

        db.add(
            InvoicePayment(
                invoice_id=locked_invoice.id,
                amount=payload.amount,
                method=payload.method,
                paid_at=payload.paid_at,
            )
        )
        db.flush()
        BillingService._sync_invoice_status(db, locked_invoice)
        db.flush()
        db.refresh(locked_invoice)
        return locked_invoice

    @staticmethod
    def _sync_invoice_status(db: Session, invoice: Invoice) -> None:
        paid_total = (
            db.query(func.coalesce(func.sum(InvoicePayment.amount), 0))
            .filter(InvoicePayment.invoice_id == invoice.id)
            .scalar()
        )
        paid_total = Decimal(paid_total)
        invoice.paid_amount = paid_total

        if paid_total <= 0:
            invoice.status = InvoiceStatus.unpaid
        elif paid_total >= Decimal(invoice.total_amount):
            invoice.status = InvoiceStatus.paid
        else:
            invoice.status = InvoiceStatus.partial

    @staticmethod
    def get_shop_invoices(db: Session, shop_id: UUID, skip: int, limit: int):
        return (
            db.query(Invoice)
            .filter(Invoice.shop_id == shop_id)
            .options(selectinload(Invoice.items), selectinload(Invoice.payments))
            .order_by(Invoice.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
