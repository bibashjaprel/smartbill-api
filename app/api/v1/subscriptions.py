from datetime import datetime, timedelta, timezone
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ...api.deps import get_current_active_user, get_current_shop, require_shop_roles
from ...api.role_sets import SHOP_ROLE_OWNER_ADMIN, SHOP_ROLE_OWNER_ONLY
from ...core.database import get_db
from ...core.transaction import write_transaction
from ...models.enums import ShopRole
from ...models.enums import AuditAction
from ...models.idempotency_key import IdempotencyKey
from ...models.shop import Shop
from ...models.subscription import Plan, Subscription
from ...models.user import User
from ...modules.audit.service import AuditService
from ...modules.subscriptions.service import SubscriptionService
from ...schemas.audit import AuditLogCreate
from ...schemas.subscription import (
    FeatureAccessRead,
    PlanRead,
    SubscriptionCreate,
    SubscriptionPaymentCreate,
    SubscriptionPaymentRead,
    SubscriptionRead,
)
from ...utils.api_response import success_response
from ...utils.idempotency import build_request_hash, get_active_idempotency_record

router = APIRouter()


@router.get("/shops/{shop_id}/plans")
def list_plans(request: Request, db: Session = Depends(get_db), shop: Shop = Depends(get_current_shop)):
    plans = db.query(Plan).filter(Plan.is_active.is_(True)).order_by(Plan.price.asc()).all()
    return success_response(
        [PlanRead.model_validate(plan).model_dump(mode="json") for plan in plans],
        request_id=getattr(request.state, "request_id", None),
    )


@router.get("/shops/{shop_id}/subscriptions")
def list_shop_subscriptions(
    request: Request,
    db: Session = Depends(get_db),
    shop: Shop = Depends(get_current_shop),
    _role=Depends(require_shop_roles(SHOP_ROLE_OWNER_ADMIN)),
):
    rows = (
        db.query(Subscription)
        .filter(Subscription.shop_id == shop.id)
        .order_by(Subscription.created_at.desc())
        .all()
    )
    return success_response(
        [SubscriptionRead.model_validate(row).model_dump(mode="json") for row in rows],
        request_id=getattr(request.state, "request_id", None),
    )


@router.post("/shops/{shop_id}/subscriptions")
def create_subscription(
    payload: SubscriptionCreate,
    request: Request,
    db: Session = Depends(get_db),
    shop: Shop = Depends(get_current_shop),
    _role=Depends(require_shop_roles(SHOP_ROLE_OWNER_ONLY)),
):
    plan = db.query(Plan).filter(Plan.id == payload.plan_id, Plan.is_active.is_(True)).first()
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
    with write_transaction(db):
        row = SubscriptionService.create_subscription(db, shop.id, payload)
    return success_response(
        SubscriptionRead.model_validate(row).model_dump(mode="json"),
        request_id=getattr(request.state, "request_id", None),
    )


@router.post("/shops/{shop_id}/subscriptions/{subscription_id}/payments")
def create_subscription_payment(
    subscription_id: UUID,
    payload: SubscriptionPaymentCreate,
    request: Request,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    shop: Shop = Depends(get_current_shop),
    _role=Depends(require_shop_roles(SHOP_ROLE_OWNER_ADMIN)),
):
    subscription = (
        db.query(Subscription)
        .filter(Subscription.id == subscription_id, Subscription.shop_id == shop.id)
        .first()
    )
    if not subscription:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")

    idempotency_scope = "subscription_payment_create"
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
            result = SubscriptionService.create_payment(db, subscription.id, payload)
            response_payload = success_response(
                SubscriptionPaymentRead.model_validate(result).model_dump(mode="json"),
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
                    action=AuditAction.create,
                    entity_type="subscription_payment",
                    entity_id=str(result.id),
                    metadata={
                        "subscription_id": str(subscription.id),
                        "amount": str(payload.amount),
                        "provider": payload.provider.value,
                        "status": payload.status.value,
                    },
                ),
            )
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


@router.get("/shops/{shop_id}/feature-access")
def get_feature_access(
    request: Request,
    feature_key: str = Query(...),
    db: Session = Depends(get_db),
    shop: Shop = Depends(get_current_shop),
):
    allowed, limit, used, reason = SubscriptionService.check_feature_access(db, shop.id, feature_key)
    payload = FeatureAccessRead(shop_id=shop.id, is_allowed=allowed, reason=reason, limit=limit, used=used)
    return success_response(
        FeatureAccessRead.model_validate(payload).model_dump(mode="json"),
        request_id=getattr(request.state, "request_id", None),
    )
