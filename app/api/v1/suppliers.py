from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ...api.deps import get_current_active_user, get_current_shop, require_shop_roles
from ...core.database import get_db
from ...crud.shop import shop as crud_shop
from ...crud.supplier import supplier as crud_supplier
from ...models.enums import ShopRole
from ...models.shop import Shop
from ...models.user import User
from ...schemas.supplier import SupplierCreate, SupplierRead, SupplierUpdate

router = APIRouter()


@router.get("/shops/{shop_id}/suppliers", response_model=List[SupplierRead])
def list_shop_suppliers(
    shop: Shop = Depends(get_current_shop),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=200),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    _role=Depends(require_shop_roles({ShopRole.owner, ShopRole.admin, ShopRole.staff})),
):
    if search and search.strip():
        return crud_supplier.search_by_shop(db, shop_id=shop.id, query=search.strip(), skip=skip, limit=limit)
    return crud_supplier.get_by_shop(db, shop_id=shop.id, skip=skip, limit=limit)


@router.post("/shops/{shop_id}/suppliers", response_model=SupplierRead)
def create_shop_supplier(
    payload: SupplierCreate,
    shop: Shop = Depends(get_current_shop),
    db: Session = Depends(get_db),
    _role=Depends(require_shop_roles({ShopRole.owner, ShopRole.admin})),
):
    payload.shop_id = shop.id
    return crud_supplier.create(db, obj_in=payload)


@router.put("/shops/{shop_id}/suppliers/{supplier_id}", response_model=SupplierRead)
def update_shop_supplier(
    supplier_id: UUID,
    payload: SupplierUpdate,
    shop: Shop = Depends(get_current_shop),
    db: Session = Depends(get_db),
    _role=Depends(require_shop_roles({ShopRole.owner, ShopRole.admin})),
):
    supplier_row = crud_supplier.get_by_shop_and_id(db, shop_id=shop.id, supplier_id=supplier_id)
    if not supplier_row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found")
    return crud_supplier.update(db, db_obj=supplier_row, obj_in=payload)


@router.delete("/shops/{shop_id}/suppliers/{supplier_id}")
def delete_shop_supplier(
    supplier_id: UUID,
    shop: Shop = Depends(get_current_shop),
    db: Session = Depends(get_db),
    _role=Depends(require_shop_roles({ShopRole.owner, ShopRole.admin})),
):
    supplier_row = crud_supplier.get_by_shop_and_id(db, shop_id=shop.id, supplier_id=supplier_id)
    if not supplier_row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found")

    db.delete(supplier_row)
    db.commit()
    return {"message": "Supplier deleted successfully"}


@router.get("/suppliers", response_model=List[SupplierRead])
def list_suppliers_fallback(
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
            return []
        target_shop_id = user_shops[0].id

    search_term = (search or q or "").strip()
    if search_term:
        return crud_supplier.search_by_shop(db, shop_id=target_shop_id, query=search_term, skip=skip, limit=limit)
    return crud_supplier.get_by_shop(db, shop_id=target_shop_id, skip=skip, limit=limit)


@router.get("/suppliers/", response_model=List[SupplierRead])
def list_suppliers_fallback_slash(
    shop_id: Optional[UUID] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=200),
    search: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return list_suppliers_fallback(
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
    return crud_supplier.create(db, obj_in=payload)


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

    return crud_supplier.update(db, db_obj=supplier_row, obj_in=payload)


@router.delete("/suppliers/{supplier_id}")
def delete_supplier_fallback(
    supplier_id: UUID,
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
    return {"message": "Supplier deleted successfully"}
