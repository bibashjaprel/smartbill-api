from uuid import UUID

from sqlalchemy.orm import Session

from ...models.inventory_alert import InventoryAlert
from ...models.product import Product
from ...models.stock_movement import StockMovement
from ...schemas.inventory import InventoryAlertCreate, StockMovementCreateV2


class InventoryService:
    @staticmethod
    def create_stock_movement(db: Session, shop_id: UUID, actor_user_id: UUID, payload: StockMovementCreateV2) -> StockMovement:
        product = db.query(Product).filter(Product.id == payload.product_id, Product.shop_id == shop_id).first()
        if not product:
            raise ValueError("Product not found for shop")

        before = int(product.stock_quantity or 0)
        after = before + int(payload.quantity_change)
        if after < 0:
            raise ValueError("Insufficient stock")

        product.stock_quantity = after
        movement = StockMovement(
            shop_id=shop_id,
            product_id=product.id,
            actor_user_id=actor_user_id,
            movement_type=payload.movement_type,
            quantity_change=payload.quantity_change,
            quantity_before=before,
            quantity_after=after,
            reason=payload.reason,
            reference_type=payload.reference_type,
            reference_id=payload.reference_id,
            unit_cost=product.cost_price,
        )
        db.add(movement)
        db.commit()
        db.refresh(movement)
        return movement

    @staticmethod
    def upsert_inventory_alert(db: Session, shop_id: UUID, payload: InventoryAlertCreate) -> InventoryAlert:
        alert = (
            db.query(InventoryAlert)
            .filter(InventoryAlert.shop_id == shop_id, InventoryAlert.product_id == payload.product_id)
            .first()
        )
        if not alert:
            alert = InventoryAlert(shop_id=shop_id, product_id=payload.product_id, threshold_quantity=payload.threshold_quantity)
            db.add(alert)
        else:
            alert.threshold_quantity = payload.threshold_quantity

        db.commit()
        db.refresh(alert)
        return alert
