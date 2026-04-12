from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ...api.deps import check_shop_subscription, get_current_active_user, get_current_shop, require_shop_roles
from ...core.database import get_db
from ...models.enums import ShopRole
from ...models.inventory_alert import InventoryAlert
from ...models.shop import Shop
from ...models.stock_movement import StockMovement
from ...models.user import User
from ...modules.inventory.service import InventoryService
from ...schemas.inventory import InventoryAlertCreate, InventoryAlertRead, StockMovementCreateV2
from ...schemas.stock_movement import StockMovementInDB

router = APIRouter()


@router.get("/shops/{shop_id}/stock-movements", response_model=List[StockMovementInDB])
def list_stock_movements(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    shop: Shop = Depends(get_current_shop),
    _role=Depends(require_shop_roles({ShopRole.owner, ShopRole.admin, ShopRole.staff})),
):
    return (
        db.query(StockMovement)
        .filter(StockMovement.shop_id == shop.id)
        .order_by(StockMovement.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.post("/shops/{shop_id}/stock-movements", response_model=StockMovementInDB)
def create_stock_movement(
    payload: StockMovementCreateV2,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    shop: Shop = Depends(get_current_shop),
    _sub=Depends(check_shop_subscription("max_products")),
    _role=Depends(require_shop_roles({ShopRole.owner, ShopRole.admin, ShopRole.staff})),
):
    try:
        return InventoryService.create_stock_movement(db, shop.id, current_user.id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/shops/{shop_id}/inventory-alerts", response_model=InventoryAlertRead)
def upsert_inventory_alert(
    payload: InventoryAlertCreate,
    db: Session = Depends(get_db),
    shop: Shop = Depends(get_current_shop),
    _role=Depends(require_shop_roles({ShopRole.owner, ShopRole.admin})),
):
    return InventoryService.upsert_inventory_alert(db, shop.id, payload)


@router.get("/shops/{shop_id}/inventory-alerts", response_model=List[InventoryAlertRead])
def list_inventory_alerts(
    db: Session = Depends(get_db),
    shop: Shop = Depends(get_current_shop),
    _role=Depends(require_shop_roles({ShopRole.owner, ShopRole.admin, ShopRole.staff})),
):
    return db.query(InventoryAlert).filter(InventoryAlert.shop_id == shop.id).order_by(InventoryAlert.created_at.desc()).all()
