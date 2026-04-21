from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional, Tuple
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from ...models.product import Product
from ...models.enums import BillingCycle, SubscriptionStatus
from ...models.invoice import Invoice
from ...models.subscription import Payment, Plan, Subscription
from ...models.user_shop_role import UserShopRole
from ...schemas.subscription import SubscriptionCreate, SubscriptionPaymentCreate


class SubscriptionService:
    TRIAL_PLAN_NAME = "trial"
    TRIAL_DAYS = 14
    DEFAULT_TRIAL_FEATURES = {
        "max_bills": 1000,
        "max_products": 200,
        "max_users": 50,
    }

    @staticmethod
    def get_or_create_trial_plan(db: Session) -> Plan:
        plan = db.query(Plan).filter(Plan.name == SubscriptionService.TRIAL_PLAN_NAME).first()
        if plan:
            return plan

        plan = Plan(
            name=SubscriptionService.TRIAL_PLAN_NAME,
            price=Decimal("0.00"),
            billing_cycle=BillingCycle.monthly,
            features=SubscriptionService.DEFAULT_TRIAL_FEATURES,
            is_active=True,
        )
        db.add(plan)
        db.flush()
        db.refresh(plan)
        return plan

    @staticmethod
    def create_trial_subscription_for_shop(db: Session, shop_id: UUID) -> Subscription:
        now = datetime.now(timezone.utc)
        existing = (
            db.query(Subscription)
            .filter(
                Subscription.shop_id == shop_id,
                Subscription.status.in_([SubscriptionStatus.trial, SubscriptionStatus.active]),
                Subscription.current_period_end >= now,
            )
            .order_by(Subscription.created_at.desc())
            .first()
        )
        if existing:
            return existing

        trial_plan = SubscriptionService.get_or_create_trial_plan(db)
        trial_end = now + timedelta(days=SubscriptionService.TRIAL_DAYS)

        subscription = Subscription(
            shop_id=shop_id,
            plan_id=trial_plan.id,
            status=SubscriptionStatus.trial,
            start_date=now,
            end_date=trial_end,
            trial_end=trial_end,
            current_period_start=now,
            current_period_end=trial_end,
        )
        db.add(subscription)
        db.flush()
        db.refresh(subscription)
        return subscription

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
        db.flush()
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
        db.flush()
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
        if feature_key == "max_bills":
            return db.query(func.count(Invoice.id)).filter(Invoice.shop_id == shop_id).scalar() or 0
        if feature_key == "max_products":
            return db.query(func.count(Product.id)).filter(Product.shop_id == shop_id).scalar() or 0
        if feature_key == "max_users":
            return db.query(func.count(UserShopRole.id)).filter(UserShopRole.shop_id == shop_id, UserShopRole.is_active.is_(True)).scalar() or 0
        return 0
