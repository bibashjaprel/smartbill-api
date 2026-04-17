from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ...core.database import get_db
from ...core.transaction import write_transaction
from ...crud.user import user as crud_user
from ...crud.shop import shop as crud_shop
from ...schemas.user import User, UserUpdate, UserProfile, UserShop, SetCurrentShopRequest
from ...schemas.shop import Shop
from ...api.deps import get_current_active_user

router = APIRouter()


@router.get("/me", response_model=User)
def read_user_me(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current user
    """
    return current_user


@router.put("/me", response_model=User)
def update_user_me(
    *,
    db: Session = Depends(get_db),
    user_in: UserUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """
    Update own user
    """
    with write_transaction(db):
        user = crud_user.update(db, db_obj=current_user, obj_in=user_in)
    return user


@router.get("/shops", response_model=List[UserShop])
def get_user_shops(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get all shops where user is a member with their roles
    """
    try:
        # For now, get shops owned by user (can be extended to include member shops)
        shops = crud_shop.get_by_owner(db, owner_id=str(current_user.id))
        current_shop_id = str(shops[0].id) if shops else None
        
        user_shops = []
        for i, shop in enumerate(shops):
            is_current = str(shop.id) == current_shop_id if current_shop_id else i == 0
            user_shops.append(UserShop(
                shop_id=shop.id,
                shop_name=shop.name,
                role=current_user.role,
                is_current=is_current,
                joined_at=shop.created_at
            ))
        
        return user_shops
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching user shops: {str(e)}"
        )


@router.get("/current-shop", response_model=Shop)
def get_current_shop(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get user's currently active shop
    """
    try:
        shops = crud_shop.get_by_owner(db, owner_id=str(current_user.id))
        if not shops:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No shops found for the current user"
            )

        # Fallback to first owned shop.
        return shops[0]
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching current shop: {str(e)}"
        )


@router.post("/current-shop/{shop_id}")
def set_current_shop(
    shop_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Switch to a different shop as current active shop
    """
    try:
        # Verify user has access to this shop
        shops = crud_shop.get_by_owner(db, owner_id=str(current_user.id))
        shop_ids = [str(shop.id) for shop in shops]
        
        if shop_id not in shop_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this shop"
            )

        return {
            "message": "Current shop pointer is deprecated; selected shop is valid for this user.",
            "current_shop_id": shop_id
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error setting current shop: {str(e)}"
        )


@router.get("/profile", response_model=UserProfile)
def get_user_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get complete user profile with shops and current shop
    """
    try:
        # Get user shops
        shops = crud_shop.get_by_owner(db, owner_id=str(current_user.id))
        
        user_shops = []
        current_shop = None
        current_shop_id = str(shops[0].id) if shops else None
        
        for i, shop in enumerate(shops):
            is_current = str(shop.id) == current_shop_id if current_shop_id else i == 0
            if is_current:
                current_shop = shop
                
            user_shops.append(UserShop(
                shop_id=shop.id,
                shop_name=shop.name,
                role=current_user.role,
                is_current=is_current,
                joined_at=shop.created_at
            ))
        
        # Create profile with additional data
        profile_data = current_user.dict()
        profile_data.update({
            "current_shop_id": current_shop.id if current_shop else None,
            "shops": user_shops
        })
        
        return UserProfile(**profile_data)
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching user profile: {str(e)}"
        )
