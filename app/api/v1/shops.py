from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ...core.database import get_db
from ...crud.shop import shop as crud_shop
from ...schemas.shop import Shop, ShopCreate, ShopUpdate, ShopWithDetails
from ...api.deps import get_current_active_user, get_user_shop
from ...models.user import User

router = APIRouter()


@router.get("/", response_model=List[Shop])
def read_shops(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Retrieve shops for current user
    """
    shops = crud_shop.get_by_owner(db, owner_id=str(current_user.id))
    return shops


@router.get("/current", response_model=Shop)
def get_current_shop(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get the current user's default shop (first shop)
    """
    shops = crud_shop.get_by_owner(db, owner_id=str(current_user.id))
    if not shops:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No shops found for the current user"
        )
    # Return the first shop as the current shop
    return shops[0]


@router.post("/", response_model=Shop)
def create_shop(
    *,
    db: Session = Depends(get_db),
    shop_in: ShopCreate,
    current_user: User = Depends(get_current_active_user)
):
    """
    Create new shop
    """
    shop = crud_shop.create_with_owner(
        db, obj_in=shop_in, owner_id=str(current_user.id)
    )
    return shop


@router.get("/{shop_id}", response_model=Shop)
def read_shop(
    *,
    shop_id: str,
    shop: Shop = Depends(get_user_shop)
):
    """
    Get shop by ID
    """
    return shop


@router.put("/{shop_id}", response_model=Shop)
def update_shop(
    *,
    db: Session = Depends(get_db),
    shop_id: str,
    shop_in: ShopUpdate,
    shop: Shop = Depends(get_user_shop)
):
    """
    Update a shop
    """
    shop = crud_shop.update(db, db_obj=shop, obj_in=shop_in)
    return shop


@router.delete("/{shop_id}")
def delete_shop(
    *,
    db: Session = Depends(get_db),
    shop_id: str,
    shop: Shop = Depends(get_user_shop)
):
    """
    Delete a shop
    """
    shop = crud_shop.remove(db, id=shop_id)
    return {"message": "Shop deleted successfully"}
