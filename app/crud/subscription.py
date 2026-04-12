from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from ..models.subscription import Payment, Plan, Subscription
from ..schemas.subscription import PlanCreate, SubscriptionCreate, SubscriptionPaymentCreate
from .base import CRUDBase


class CRUDPlan(CRUDBase[Plan, PlanCreate, dict]):
    def get_active(self, db: Session) -> List[Plan]:
        return db.query(Plan).filter(Plan.is_active.is_(True)).order_by(Plan.price.asc()).all()


class CRUDSubscription(CRUDBase[Subscription, SubscriptionCreate, dict]):
    def get_by_shop(self, db: Session, *, shop_id: UUID) -> List[Subscription]:
        return (
            db.query(Subscription)
            .filter(Subscription.shop_id == shop_id)
            .order_by(Subscription.created_at.desc())
            .all()
        )

    def get_by_shop_and_id(self, db: Session, *, shop_id: UUID, subscription_id: UUID) -> Optional[Subscription]:
        return (
            db.query(Subscription)
            .filter(Subscription.shop_id == shop_id, Subscription.id == subscription_id)
            .first()
        )


class CRUDSubscriptionPayment(CRUDBase[Payment, SubscriptionPaymentCreate, dict]):
    def get_by_subscription(self, db: Session, *, subscription_id: UUID) -> List[Payment]:
        return (
            db.query(Payment)
            .filter(Payment.subscription_id == subscription_id)
            .order_by(Payment.created_at.desc())
            .all()
        )


plan = CRUDPlan(Plan)
subscription = CRUDSubscription(Subscription)
subscription_payment = CRUDSubscriptionPayment(Payment)
