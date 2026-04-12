from datetime import datetime
from typing import Optional
import uuid

from pydantic import BaseModel, ConfigDict, Field

from ..models.enums import StockMovementType


class InventoryAlertCreate(BaseModel):
    product_id: uuid.UUID
    threshold_quantity: int = Field(..., ge=0)


class InventoryAlertRead(InventoryAlertCreate):
    id: uuid.UUID
    shop_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StockMovementCreateV2(BaseModel):
    product_id: uuid.UUID
    movement_type: StockMovementType
    quantity_change: int
    reason: Optional[str] = None
    reference_type: Optional[str] = None
    reference_id: Optional[str] = None
