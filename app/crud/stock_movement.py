from sqlalchemy.orm import Session
from typing import List, Optional
import uuid

from ..models.stock_movement import StockMovement
from ..schemas.stock_movement import StockMovementCreate


class CRUDStockMovement:
    def create(
        self,
        db: Session,
        *,
        shop_id: uuid.UUID,
        actor_user_id: Optional[uuid.UUID],
        quantity_before: int,
        quantity_after: int,
        obj_in: StockMovementCreate,
    ) -> StockMovement:
        total_cost_impact = None
        if obj_in.unit_cost is not None:
            total_cost_impact = obj_in.unit_cost * abs(obj_in.quantity_change)

        db_obj = StockMovement(
            shop_id=shop_id,
            product_id=obj_in.product_id,
            actor_user_id=actor_user_id,
            movement_type=obj_in.movement_type,
            quantity_change=obj_in.quantity_change,
            quantity_before=quantity_before,
            quantity_after=quantity_after,
            reason=obj_in.reason,
            reference_type=obj_in.reference_type,
            reference_id=obj_in.reference_id,
            unit_cost=obj_in.unit_cost,
            total_cost_impact=total_cost_impact,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_by_shop(
        self,
        db: Session,
        *,
        shop_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> List[StockMovement]:
        return (
            db.query(StockMovement)
            .filter(StockMovement.shop_id == shop_id)
            .order_by(StockMovement.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )


stock_movement = CRUDStockMovement()
