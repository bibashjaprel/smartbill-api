from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ...api.deps import get_current_shop, require_shop_roles
from ...core.database import get_db
from ...models.enums import ShopRole
from ...models.shop import Shop
from ...modules.credit.service import CreditService
from ...schemas.credit import CreditLedgerRead, CreditPaymentCreate, CustomerCreditSummary
from ...schemas.invoice import InvoiceRead

router = APIRouter()


@router.get("/shops/{shop_id}/customers/{customer_id}/credit/summary", response_model=CustomerCreditSummary)
def get_credit_summary(
    customer_id: UUID,
    db: Session = Depends(get_db),
    shop: Shop = Depends(get_current_shop),
    _role=Depends(require_shop_roles({ShopRole.owner, ShopRole.admin, ShopRole.staff})),
):
    return CreditService.get_customer_summary(db, shop.id, customer_id)


@router.get("/shops/{shop_id}/customers/{customer_id}/credit/ledger", response_model=CreditLedgerRead)
def get_credit_ledger(
    customer_id: UUID,
    db: Session = Depends(get_db),
    shop: Shop = Depends(get_current_shop),
    _role=Depends(require_shop_roles({ShopRole.owner, ShopRole.admin, ShopRole.staff})),
):
    return CreditService.get_customer_ledger(db, shop.id, customer_id)


@router.post("/shops/{shop_id}/customers/{customer_id}/credit/payments", response_model=InvoiceRead)
def apply_credit_payment(
    customer_id: UUID,
    payload: CreditPaymentCreate,
    db: Session = Depends(get_db),
    shop: Shop = Depends(get_current_shop),
    _role=Depends(require_shop_roles({ShopRole.owner, ShopRole.admin, ShopRole.staff})),
):
    try:
        return CreditService.apply_payment(db, shop.id, customer_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
