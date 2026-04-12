from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ...api.deps import get_current_shop, require_shop_roles
from ...core.database import get_db
from ...models.enums import ShopRole
from ...models.shop import Shop
from ...models.subscription import Plan, Subscription
from ...modules.subscriptions.service import SubscriptionService
from ...schemas.subscription import (
    FeatureAccessRead,
    PlanRead,
    SubscriptionCreate,
    SubscriptionPaymentCreate,
    SubscriptionPaymentRead,
    SubscriptionRead,
)

router = APIRouter()


@router.get("/shops/{shop_id}/plans", response_model=List[PlanRead])
def list_plans(db: Session = Depends(get_db), shop: Shop = Depends(get_current_shop)):
    return db.query(Plan).filter(Plan.is_active.is_(True)).order_by(Plan.price.asc()).all()


@router.get("/shops/{shop_id}/subscriptions", response_model=List[SubscriptionRead])
def list_shop_subscriptions(
    db: Session = Depends(get_db),
    shop: Shop = Depends(get_current_shop),
    _role=Depends(require_shop_roles({ShopRole.owner, ShopRole.admin})),
):
    return (
        db.query(Subscription)
        .filter(Subscription.shop_id == shop.id)
        .order_by(Subscription.created_at.desc())
        .all()
    )


@router.post("/shops/{shop_id}/subscriptions", response_model=SubscriptionRead)
def create_subscription(
    payload: SubscriptionCreate,
    db: Session = Depends(get_db),
    shop: Shop = Depends(get_current_shop),
    _role=Depends(require_shop_roles({ShopRole.owner})),
):
    plan = db.query(Plan).filter(Plan.id == payload.plan_id, Plan.is_active.is_(True)).first()
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
    return SubscriptionService.create_subscription(db, shop.id, payload)


@router.post("/shops/{shop_id}/subscriptions/{subscription_id}/payments", response_model=SubscriptionPaymentRead)
def create_subscription_payment(
    subscription_id: UUID,
    payload: SubscriptionPaymentCreate,
    db: Session = Depends(get_db),
    shop: Shop = Depends(get_current_shop),
    _role=Depends(require_shop_roles({ShopRole.owner, ShopRole.admin})),
):
    subscription = (
        db.query(Subscription)
        .filter(Subscription.id == subscription_id, Subscription.shop_id == shop.id)
        .first()
    )
    if not subscription:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")
    return SubscriptionService.create_payment(db, subscription.id, payload)


@router.get("/shops/{shop_id}/feature-access", response_model=FeatureAccessRead)
def get_feature_access(
    feature_key: str = Query(...),
    db: Session = Depends(get_db),
    shop: Shop = Depends(get_current_shop),
):
    allowed, limit, used, reason = SubscriptionService.check_feature_access(db, shop.id, feature_key)
    return FeatureAccessRead(shop_id=shop.id, is_allowed=allowed, reason=reason, limit=limit, used=used)
