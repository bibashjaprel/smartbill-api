from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from ..models.inventory_alert import InventoryAlert
from ..schemas.inventory import InventoryAlertCreate
from .base import CRUDBase


class CRUDInventoryAlert(CRUDBase[InventoryAlert, InventoryAlertCreate, dict]):
    def get_by_shop(self, db: Session, *, shop_id: UUID) -> List[InventoryAlert]:
        return (
            db.query(InventoryAlert)
            .filter(InventoryAlert.shop_id == shop_id)
            .order_by(InventoryAlert.created_at.desc())
            .all()
        )

    def get_by_shop_and_product(self, db: Session, *, shop_id: UUID, product_id: UUID) -> Optional[InventoryAlert]:
        return (
            db.query(InventoryAlert)
            .filter(InventoryAlert.shop_id == shop_id, InventoryAlert.product_id == product_id)
            .first()
        )


inventory_alert = CRUDInventoryAlert(InventoryAlert)
