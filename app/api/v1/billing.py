from datetime import datetime, timedelta, timezone
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ...api.deps import check_shop_subscription, get_current_active_user, get_current_shop, require_shop_roles
from ...api.role_sets import SHOP_ROLE_OWNER_ADMIN_STAFF
from ...core.database import get_db
from ...core.transaction import write_transaction
from ...models.enums import ShopRole
from ...models.idempotency_key import IdempotencyKey
from ...models.invoice import Invoice
from ...models.shop import Shop
from ...models.user import User
from ...modules.billing.service import BillingService
from ...schemas.invoice import InvoiceCreate, InvoicePaymentCreate, InvoiceRead
from ...utils.api_response import success_response
from ...utils.idempotency import build_request_hash, get_active_idempotency_record

router = APIRouter()


@router.get("/shops/{shop_id}/invoices")
def list_shop_invoices(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    shop: Shop = Depends(get_current_shop),
    _role=Depends(require_shop_roles(SHOP_ROLE_OWNER_ADMIN_STAFF)),
):
    items = BillingService.get_shop_invoices(db, shop.id, skip, limit)
    return success_response(
        [InvoiceRead.model_validate(item).model_dump(mode="json") for item in items],
        request_id=getattr(request.state, "request_id", None),
        meta={"pagination": {"skip": skip, "limit": limit, "has_more": len(items) == limit}},
    )


@router.post("/shops/{shop_id}/invoices")
def create_invoice(
    payload: InvoiceCreate,
    request: Request,
    db: Session = Depends(get_db),
    shop: Shop = Depends(get_current_shop),
    _sub=Depends(check_shop_subscription("max_bills")),
    _role=Depends(require_shop_roles(SHOP_ROLE_OWNER_ADMIN_STAFF)),
):
    try:
        with write_transaction(db):
            created = BillingService.create_invoice(db, shop.id, payload)
        return success_response(
            InvoiceRead.model_validate(created).model_dump(mode="json"),
            request_id=getattr(request.state, "request_id", None),
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/shops/{shop_id}/invoices/{invoice_id}/payments")
def add_invoice_payment(
    invoice_id: UUID,
    payload: InvoicePaymentCreate,
    request: Request,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    shop: Shop = Depends(get_current_shop),
    _role=Depends(require_shop_roles(SHOP_ROLE_OWNER_ADMIN_STAFF)),
):
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id, Invoice.shop_id == shop.id).first()
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")

    idempotency_scope = "invoice_payment_create"
    request_hash = None
    if idempotency_key:
        request_hash = build_request_hash(payload)
        existing = get_active_idempotency_record(
            db,
            key=idempotency_key,
            endpoint=idempotency_scope,
            user_id=current_user.id,
            shop_id=shop.id,
        )
        if existing:
            if existing.request_hash != request_hash:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Idempotency key was reused with a different payload",
                )
            return existing.response_body

    try:
        with write_transaction(db):
            result = BillingService.add_payment(db, invoice, payload)
            response_payload = success_response(
                InvoiceRead.model_validate(result).model_dump(mode="json"),
                request_id=getattr(request.state, "request_id", None),
            )

            if idempotency_key and request_hash:
                db.add(
                    IdempotencyKey(
                        key=idempotency_key,
                        endpoint=idempotency_scope,
                        user_id=current_user.id,
                        shop_id=shop.id,
                        request_hash=request_hash,
                        status_code=200,
                        response_body=response_payload,
                        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
                    )
                )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except IntegrityError:
        existing = get_active_idempotency_record(
            db,
            key=idempotency_key,
            endpoint=idempotency_scope,
            user_id=current_user.id,
            shop_id=shop.id,
        )
        if existing:
            return existing.response_body
        raise

    return response_payload
