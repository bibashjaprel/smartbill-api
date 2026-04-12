from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal
import uuid


class StockMovementBase(BaseModel):
    product_id: uuid.UUID
    movement_type: str = Field(..., description="in, out, adjustment, return, damage, transfer")
    quantity_change: int
    reason: Optional[str] = None
    reference_type: Optional[str] = None
    reference_id: Optional[str] = None
    unit_cost: Optional[Decimal] = None


class StockMovementCreate(StockMovementBase):
    pass


class StockMovementInDB(StockMovementBase):
    id: uuid.UUID
    shop_id: uuid.UUID
    actor_user_id: Optional[uuid.UUID] = None
    quantity_before: int
    quantity_after: int
    total_cost_impact: Optional[Decimal] = None
    created_at: datetime

    class Config:
        from_attributes = True
