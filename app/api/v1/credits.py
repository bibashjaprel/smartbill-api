from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ...api.deps import get_current_active_user, get_current_shop, require_shop_roles
from ...api.role_sets import SHOP_ROLE_OWNER_ADMIN_STAFF
from ...core.database import get_db
from ...core.transaction import write_transaction
from ...models.enums import ShopRole
from ...models.enums import AuditAction
from ...models.idempotency_key import IdempotencyKey
from ...models.shop import Shop
from ...models.user import User
from ...modules.audit.service import AuditService
from ...modules.credit.service import CreditService
from ...schemas.audit import AuditLogCreate
from ...schemas.credit import CreditLedgerRead, CreditPaymentCreate, CustomerCreditSummary
from ...schemas.invoice import InvoiceRead
from ...utils.api_response import success_response
from ...utils.idempotency import build_request_hash, get_active_idempotency_record

router = APIRouter()


@router.get("/shops/{shop_id}/customers/{customer_id}/credit/summary")
def get_credit_summary(
    customer_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    shop: Shop = Depends(get_current_shop),
    _role=Depends(require_shop_roles(SHOP_ROLE_OWNER_ADMIN_STAFF)),
):
    summary = CreditService.get_customer_summary(db, shop.id, customer_id)
    return success_response(
        CustomerCreditSummary.model_validate(summary).model_dump(mode="json"),
        request_id=getattr(request.state, "request_id", None),
    )


@router.get("/shops/{shop_id}/customers/{customer_id}/credit/ledger")
def get_credit_ledger(
    customer_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    shop: Shop = Depends(get_current_shop),
    _role=Depends(require_shop_roles(SHOP_ROLE_OWNER_ADMIN_STAFF)),
):
    ledger = CreditService.get_customer_ledger(db, shop.id, customer_id)
    return success_response(
        CreditLedgerRead.model_validate(ledger).model_dump(mode="json"),
        request_id=getattr(request.state, "request_id", None),
    )


@router.post("/shops/{shop_id}/customers/{customer_id}/credit/payments")
def apply_credit_payment(
    customer_id: UUID,
    payload: CreditPaymentCreate,
    request: Request,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    shop: Shop = Depends(get_current_shop),
    _role=Depends(require_shop_roles(SHOP_ROLE_OWNER_ADMIN_STAFF)),
):
    idempotency_scope = "credit_payment_apply"
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
            result = CreditService.apply_payment(db, shop.id, customer_id, payload)
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

            AuditService.log(
                db,
                user_id=current_user.id,
                payload=AuditLogCreate(
                    action=AuditAction.update,
                    entity_type="credit_payment",
                    entity_id=str(result.id),
                    metadata={
                        "customer_id": str(customer_id),
                        "invoice_id": str(payload.invoice_id),
                        "amount": str(payload.amount),
                        "method": payload.method,
                    },
                ),
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
