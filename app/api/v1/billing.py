from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ...api.deps import check_shop_subscription, get_current_shop, require_shop_roles
from ...core.database import get_db
from ...models.enums import ShopRole
from ...models.invoice import Invoice
from ...models.shop import Shop
from ...modules.billing.service import BillingService
from ...schemas.invoice import InvoiceCreate, InvoicePaymentCreate, InvoiceRead

router = APIRouter()


@router.get("/shops/{shop_id}/invoices", response_model=List[InvoiceRead])
def list_shop_invoices(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    shop: Shop = Depends(get_current_shop),
    _role=Depends(require_shop_roles({ShopRole.owner, ShopRole.admin, ShopRole.staff})),
):
    return BillingService.get_shop_invoices(db, shop.id, skip, limit)


@router.post("/shops/{shop_id}/invoices", response_model=InvoiceRead)
def create_invoice(
    payload: InvoiceCreate,
    db: Session = Depends(get_db),
    shop: Shop = Depends(get_current_shop),
    _sub=Depends(check_shop_subscription("max_products")),
    _role=Depends(require_shop_roles({ShopRole.owner, ShopRole.admin, ShopRole.staff})),
):
    try:
        return BillingService.create_invoice(db, shop.id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/shops/{shop_id}/invoices/{invoice_id}/payments", response_model=InvoiceRead)
def add_invoice_payment(
    invoice_id: UUID,
    payload: InvoicePaymentCreate,
    db: Session = Depends(get_db),
    shop: Shop = Depends(get_current_shop),
    _role=Depends(require_shop_roles({ShopRole.owner, ShopRole.admin, ShopRole.staff})),
):
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id, Invoice.shop_id == shop.id).first()
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    return BillingService.add_payment(db, invoice, payload)
