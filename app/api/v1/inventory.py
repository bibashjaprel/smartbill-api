from datetime import datetime, timedelta, timezone
from typing import List

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ...api.deps import check_shop_subscription, get_current_active_user, get_current_shop, require_shop_roles
from ...api.role_sets import SHOP_ROLE_OWNER_ADMIN, SHOP_ROLE_OWNER_ADMIN_STAFF
from ...core.database import get_db
from ...core.transaction import write_transaction
from ...models.enums import ShopRole
from ...models.enums import AuditAction
from ...models.idempotency_key import IdempotencyKey
from ...models.inventory_alert import InventoryAlert
from ...models.shop import Shop
from ...models.stock_movement import StockMovement
from ...models.user import User
from ...modules.audit.service import AuditService
from ...modules.inventory.service import InventoryService
from ...schemas.audit import AuditLogCreate
from ...schemas.inventory import InventoryAlertCreate, InventoryAlertRead, StockMovementCreateV2
from ...schemas.stock_movement import StockMovementInDB
from ...utils.api_response import success_response
from ...utils.idempotency import build_request_hash, get_active_idempotency_record

router = APIRouter()


@router.get("/shops/{shop_id}/stock-movements")
def list_stock_movements(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    shop: Shop = Depends(get_current_shop),
    _role=Depends(require_shop_roles(SHOP_ROLE_OWNER_ADMIN_STAFF)),
):
    rows = (
        db.query(StockMovement)
        .filter(StockMovement.shop_id == shop.id)
        .order_by(StockMovement.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return success_response(
        [StockMovementInDB.model_validate(row).model_dump(mode="json") for row in rows],
        request_id=getattr(request.state, "request_id", None),
        meta={"pagination": {"skip": skip, "limit": limit, "has_more": len(rows) == limit}},
    )


@router.post("/shops/{shop_id}/stock-movements")
def create_stock_movement(
    payload: StockMovementCreateV2,
    request: Request,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    shop: Shop = Depends(get_current_shop),
    _sub=Depends(check_shop_subscription("max_products")),
    _role=Depends(require_shop_roles(SHOP_ROLE_OWNER_ADMIN_STAFF)),
):
    idempotency_scope = "stock_movement_create"
    request_hash = None
    if idempotency_key:
        request_hash = build_request_hash(payload)
        existing = get_active_idempotency_record(
            db,
            key=idempotency_key,
            endpoint=idempotency_scope,
            user_id=current_user.id,
            shop_id=shop.id,
        )
        if existing:
            if existing.request_hash != request_hash:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Idempotency key was reused with a different payload",
                )
            return existing.response_body

    try:
        with write_transaction(db):
            result = InventoryService.create_stock_movement(db, shop.id, current_user.id, payload)
            response_payload = success_response(
                StockMovementInDB.model_validate(result).model_dump(mode="json"),
                request_id=getattr(request.state, "request_id", None),
            )

            if idempotency_key and request_hash:
                db.add(
                    IdempotencyKey(
                        key=idempotency_key,
                        endpoint=idempotency_scope,
                        user_id=current_user.id,
                        shop_id=shop.id,
                        request_hash=request_hash,
                        status_code=200,
                        response_body=response_payload,
                        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
                    )
                )

            AuditService.log(
                db,
                user_id=current_user.id,
                payload=AuditLogCreate(
                    action=AuditAction.create,
                    entity_type="stock_movement",
                    entity_id=str(result.id),
                    metadata={
                        "product_id": str(payload.product_id),
                        "movement_type": str(payload.movement_type),
                        "quantity_change": payload.quantity_change,
                        "reference_type": payload.reference_type,
                        "reference_id": payload.reference_id,
                    },
                ),
            )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except IntegrityError:
        existing = get_active_idempotency_record(
            db,
            key=idempotency_key,
            endpoint=idempotency_scope,
            user_id=current_user.id,
            shop_id=shop.id,
        )
        if existing:
            return existing.response_body
        raise

    return response_payload


@router.post("/shops/{shop_id}/inventory-alerts")
def upsert_inventory_alert(
    payload: InventoryAlertCreate,
    request: Request,
    db: Session = Depends(get_db),
    shop: Shop = Depends(get_current_shop),
    _role=Depends(require_shop_roles(SHOP_ROLE_OWNER_ADMIN)),
):
    with write_transaction(db):
        alert = InventoryService.upsert_inventory_alert(db, shop.id, payload)
    return success_response(
        InventoryAlertRead.model_validate(alert).model_dump(mode="json"),
        request_id=getattr(request.state, "request_id", None),
    )


@router.get("/shops/{shop_id}/inventory-alerts")
def list_inventory_alerts(
    request: Request,
    db: Session = Depends(get_db),
    shop: Shop = Depends(get_current_shop),
    _role=Depends(require_shop_roles(SHOP_ROLE_OWNER_ADMIN_STAFF)),
):
    alerts = db.query(InventoryAlert).filter(InventoryAlert.shop_id == shop.id).order_by(InventoryAlert.created_at.desc()).all()
    return success_response(
        [InventoryAlertRead.model_validate(alert).model_dump(mode="json") for alert in alerts],
        request_id=getattr(request.state, "request_id", None),
    )
