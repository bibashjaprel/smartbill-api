from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from ...api.deps import get_current_active_user, get_current_shop, require_shop_roles
from ...api.role_sets import SHOP_ROLE_OWNER_ADMIN, SHOP_ROLE_OWNER_ADMIN_STAFF
from ...core.database import get_db
from ...core.transaction import write_transaction
from ...crud.shop import shop as crud_shop
from ...crud.supplier import supplier as crud_supplier
from ...models.enums import ShopRole
from ...models.shop import Shop
from ...models.user import User
from ...schemas.supplier import SupplierCreate, SupplierRead, SupplierUpdate
from ...utils.api_response import paginated_response, success_response

router = APIRouter()


@router.get("/shops/{shop_id}/suppliers", response_model=List[SupplierRead])
def list_shop_suppliers(
    request: Request,
    shop: Shop = Depends(get_current_shop),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=200),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    _role=Depends(require_shop_roles(SHOP_ROLE_OWNER_ADMIN_STAFF)),
):
    base_query = db.query(crud_supplier.model).filter(crud_supplier.model.shop_id == shop.id)
    if search and search.strip():
        search_term = f"%{search.strip()}%"
        base_query = base_query.filter(
            crud_supplier.model.name.ilike(search_term)
            | crud_supplier.model.contact_person.ilike(search_term)
            | crud_supplier.model.phone.ilike(search_term)
            | crud_supplier.model.email.ilike(search_term)
        )

    total = base_query.count()
    rows = base_query.order_by(crud_supplier.model.created_at.desc()).offset(skip).limit(limit).all()
    return paginated_response(
        [SupplierRead.model_validate(row).model_dump(mode="json") for row in rows],
        total=total,
        limit=limit,
        skip=skip,
        request_id=getattr(request.state, "request_id", None),
    )


@router.post("/shops/{shop_id}/suppliers", response_model=SupplierRead)
def create_shop_supplier(
    payload: SupplierCreate,
    shop: Shop = Depends(get_current_shop),
    db: Session = Depends(get_db),
    _role=Depends(require_shop_roles(SHOP_ROLE_OWNER_ADMIN)),
):
    payload.shop_id = shop.id
    with write_transaction(db):
        row = crud_supplier.create(db, obj_in=payload)
    return row


@router.put("/shops/{shop_id}/suppliers/{supplier_id}", response_model=SupplierRead)
def update_shop_supplier(
    supplier_id: UUID,
    payload: SupplierUpdate,
    shop: Shop = Depends(get_current_shop),
    db: Session = Depends(get_db),
    _role=Depends(require_shop_roles(SHOP_ROLE_OWNER_ADMIN)),
):
    supplier_row = crud_supplier.get_by_shop_and_id(db, shop_id=shop.id, supplier_id=supplier_id)
    if not supplier_row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found")
    with write_transaction(db):
        row = crud_supplier.update(db, db_obj=supplier_row, obj_in=payload)
    return row


@router.delete("/shops/{shop_id}/suppliers/{supplier_id}")
def delete_shop_supplier(
    supplier_id: UUID,
    request: Request,
    shop: Shop = Depends(get_current_shop),
    db: Session = Depends(get_db),
    _role=Depends(require_shop_roles(SHOP_ROLE_OWNER_ADMIN)),
):
    supplier_row = crud_supplier.get_by_shop_and_id(db, shop_id=shop.id, supplier_id=supplier_id)
    if not supplier_row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found")

    db.delete(supplier_row)
    db.commit()
    return success_response(
        {"message": "Supplier deleted successfully"},
        request_id=getattr(request.state, "request_id", None),
    )


@router.get("/suppliers", response_model=List[SupplierRead])
def list_suppliers_fallback(
    request: Request,
    shop_id: Optional[UUID] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=200),
    search: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    target_shop_id = shop_id
    if not target_shop_id:
        user_shops = crud_shop.get_by_owner(db, owner_id=str(current_user.id))
        if not user_shops:
            return paginated_response([], total=0, limit=limit, skip=skip, request_id=getattr(request.state, "request_id", None))
        target_shop_id = user_shops[0].id

    base_query = db.query(crud_supplier.model).filter(crud_supplier.model.shop_id == target_shop_id)
    search_term = (search or q or "").strip()
    if search_term:
        like_term = f"%{search_term}%"
        base_query = base_query.filter(
            crud_supplier.model.name.ilike(like_term)
            | crud_supplier.model.contact_person.ilike(like_term)
            | crud_supplier.model.phone.ilike(like_term)
            | crud_supplier.model.email.ilike(like_term)
        )

    total = base_query.count()
    rows = base_query.order_by(crud_supplier.model.created_at.desc()).offset(skip).limit(limit).all()
    return paginated_response(
        [SupplierRead.model_validate(row).model_dump(mode="json") for row in rows],
        total=total,
        limit=limit,
        skip=skip,
        request_id=getattr(request.state, "request_id", None),
    )


@router.get("/suppliers/", response_model=List[SupplierRead])
def list_suppliers_fallback_slash(
    request: Request,
    shop_id: Optional[UUID] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=200),
    search: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return list_suppliers_fallback(
        request=request,
        shop_id=shop_id,
        skip=skip,
        limit=limit,
        search=search,
        q=q,
        db=db,
        current_user=current_user,
    )


@router.post("/suppliers", response_model=SupplierRead)
def create_supplier_fallback(
    payload: SupplierCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    target_shop_id = payload.shop_id
    if not target_shop_id:
        user_shops = crud_shop.get_by_owner(db, owner_id=str(current_user.id))
        if not user_shops:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No shops found for user")
        target_shop_id = user_shops[0].id

    payload.shop_id = target_shop_id
    with write_transaction(db):
        row = crud_supplier.create(db, obj_in=payload)
    return row


@router.put("/suppliers/{supplier_id}", response_model=SupplierRead)
def update_supplier_fallback(
    supplier_id: UUID,
    payload: SupplierUpdate,
    shop_id: UUID = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    supplier_row = crud_supplier.get_by_shop_and_id(db, shop_id=shop_id, supplier_id=supplier_id)
    if not supplier_row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found")

    shop = crud_shop.get(db, id=shop_id)
    if not shop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shop not found")

    if str(shop.owner_id) != str(current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    with write_transaction(db):
        row = crud_supplier.update(db, db_obj=supplier_row, obj_in=payload)
    return row


@router.delete("/suppliers/{supplier_id}")
def delete_supplier_fallback(
    supplier_id: UUID,
    request: Request,
    shop_id: UUID = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    supplier_row = crud_supplier.get_by_shop_and_id(db, shop_id=shop_id, supplier_id=supplier_id)
    if not supplier_row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found")

    shop = crud_shop.get(db, id=shop_id)
    if not shop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shop not found")

    if str(shop.owner_id) != str(current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    db.delete(supplier_row)
    db.commit()
    return success_response(
        {"message": "Supplier deleted successfully"},
        request_id=getattr(request.state, "request_id", None),
    )
