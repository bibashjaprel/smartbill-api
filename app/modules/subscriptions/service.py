from datetime import datetime, timezone
from typing import Optional, Tuple
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from ...models.product import Product
from ...models.subscription import Payment, Plan, Subscription
from ...models.user_shop_role import UserShopRole
from ...schemas.subscription import SubscriptionCreate, SubscriptionPaymentCreate


class SubscriptionService:
    @staticmethod
    def create_subscription(db: Session, shop_id: UUID, payload: SubscriptionCreate) -> Subscription:
        subscription = Subscription(
            shop_id=shop_id,
            plan_id=payload.plan_id,
            status=payload.status,
            start_date=payload.start_date,
            end_date=payload.end_date,
            trial_end=payload.trial_end,
            current_period_start=payload.current_period_start,
            current_period_end=payload.current_period_end,
        )
        db.add(subscription)
        db.commit()
        db.refresh(subscription)
        return subscription

    @staticmethod
    def create_payment(db: Session, subscription_id: UUID, payload: SubscriptionPaymentCreate) -> Payment:
        payment = Payment(
            subscription_id=subscription_id,
            amount=payload.amount,
            provider=payload.provider,
            transaction_ref=payload.transaction_ref,
            status=payload.status,
            paid_at=payload.paid_at,
        )
        db.add(payment)
        db.commit()
        db.refresh(payment)
        return payment

    @staticmethod
    def get_active_subscription(db: Session, shop_id: UUID) -> Optional[Subscription]:
        now = datetime.now(timezone.utc)
        return (
            db.query(Subscription)
            .filter(
                Subscription.shop_id == shop_id,
                Subscription.current_period_end >= now,
                Subscription.status.in_(["trial", "active"]),
            )
            .order_by(Subscription.created_at.desc())
            .first()
        )

    @staticmethod
    def check_feature_access(db: Session, shop_id: UUID, feature_key: str, used: Optional[int] = None) -> Tuple[bool, Optional[int], Optional[int], Optional[str]]:
        subscription = SubscriptionService.get_active_subscription(db, shop_id)
        if not subscription:
            return False, None, used, "No active subscription"

        plan = db.query(Plan).filter(Plan.id == subscription.plan_id, Plan.is_active.is_(True)).first()
        if not plan:
            return False, None, used, "Plan is not active"

        feature_value = plan.features.get(feature_key)
        if feature_value is None:
            return True, None, used, None

        if isinstance(feature_value, bool):
            return feature_value, None, used, None if feature_value else f"Feature '{feature_key}' is disabled"

        if used is None:
            used = SubscriptionService._infer_usage(db, shop_id, feature_key)

        limit_value = int(feature_value)
        if used >= limit_value:
            return False, limit_value, used, f"Limit reached for {feature_key}"
        return True, limit_value, used, None

    @staticmethod
    def _infer_usage(db: Session, shop_id: UUID, feature_key: str) -> int:
        if feature_key == "max_products":
            return db.query(func.count(Product.id)).filter(Product.shop_id == shop_id).scalar() or 0
        if feature_key == "max_users":
            return db.query(func.count(UserShopRole.id)).filter(UserShopRole.shop_id == shop_id, UserShopRole.is_active.is_(True)).scalar() or 0
        return 0
