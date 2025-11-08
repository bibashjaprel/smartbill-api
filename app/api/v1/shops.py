from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ...core.database import get_db
from ...crud.shop import shop as crud_shop
from ...crud.user import user as crud_user
from ...schemas.shop import Shop, ShopCreate, ShopUpdate, ShopWithDetails
from ...schemas.user import UserRole, UserShop
from ...api.deps import get_current_active_user, get_user_shop
from ...models.user import User

router = APIRouter()


@router.get("/", response_model=List[Shop])
def read_shops(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Retrieve shops based on user role:
    - SUPER_ADMIN/PLATFORM_ADMIN: All shops
    - SHOP_OWNER: Owned shops
    - ADMIN/MANAGER/EMPLOYEE: Current shop only
    """
    try:
        if UserRole.is_platform_role(current_user.role):
            # Platform admins can see all shops
            shops = crud_shop.get_multi(db)
        elif current_user.role == UserRole.SHOP_OWNER:
            # Shop owners see their owned shops
            shops = crud_shop.get_by_owner(db, owner_id=str(current_user.id))
        else:
            # Other roles see only their current shop
            if current_user.shop_id:
                shop = crud_shop.get(db, id=current_user.shop_id)
                shops = [shop] if shop else []
            else:
                shops = []
        
        return shops
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching shops: {str(e)}"
        )


@router.get("/current", response_model=Optional[Shop])
def get_current_shop(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get the current user's active/current shop
    """
    try:
        if not current_user.shop_id:
            return None
        
        shop = crud_shop.get(db, id=current_user.shop_id)
        if not shop:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Current shop not found"
            )
        
        # Verify user has access to this shop
        if not UserRole.is_platform_role(current_user.role):
            if current_user.role == UserRole.SHOP_OWNER and shop.owner_id != str(current_user.id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to this shop"
                )
        
        return shop
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching current shop: {str(e)}"
        )


@router.post("/current/{shop_id}")
def set_current_shop(
    *,
    shop_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Set the current/active shop for the user
    """
    try:
        # Verify shop exists
        shop = crud_shop.get(db, id=shop_id)
        if not shop:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Shop not found"
            )
        
        # Check permissions
        if not UserRole.is_platform_role(current_user.role):
            if current_user.role == UserRole.SHOP_OWNER and shop.owner_id != str(current_user.id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only set your own shops as current"
                )
            elif UserRole.is_shop_role(current_user.role) and shop.owner_id != str(current_user.id):
                # For shop-level roles, verify they have access to this shop
                # In a full implementation, this would check user-shop membership
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to this shop"
                )
        
        # Update user's current shop
        current_user.shop_id = shop_id
        db.add(current_user)
        db.commit()
        
        return {"message": f"Current shop set to {shop.name}", "shop_id": shop_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error setting current shop: {str(e)}"
        )


@router.post("/", response_model=Shop)
def create_shop(
    *,
    db: Session = Depends(get_db),
    shop_in: ShopCreate,
    current_user: User = Depends(get_current_active_user)
):
    """
    Create new shop. Permissions:
    - SUPER_ADMIN/PLATFORM_ADMIN: Can create shops for any owner
    - SHOP_OWNER: Can create their own shops
    - Others: Not allowed
    """
    try:
        # Check permissions
        if not UserRole.can_access(current_user.role, UserRole.SHOP_OWNER):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to create a shop"
            )
        
        # Set owner_id based on role
        if UserRole.is_platform_role(current_user.role):
            # Platform admins can specify owner in the request or default to themselves
            owner_id = getattr(shop_in, 'owner_id', str(current_user.id))
        else:
            # Shop owners can only create shops for themselves
            owner_id = str(current_user.id)
        
        shop = crud_shop.create_with_owner(
            db, obj_in=shop_in, owner_id=owner_id
        )
        
        # If this is the user's first shop, set it as current
        if owner_id == str(current_user.id) and not current_user.shop_id:
            current_user.shop_id = str(shop.id)
            db.add(current_user)
            db.commit()
        
        return shop
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating shop: {str(e)}"
        )


@router.get("/{shop_id}", response_model=Shop)
def read_shop(
    *,
    shop_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get shop by ID with proper permissions check
    """
    try:
        shop = crud_shop.get(db, id=shop_id)
        if not shop:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Shop not found"
            )
        
        # Check permissions
        if not UserRole.is_platform_role(current_user.role):
            if current_user.role == UserRole.SHOP_OWNER and shop.owner_id != str(current_user.id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to this shop"
                )
            elif UserRole.is_shop_role(current_user.role) and current_user.shop_id != shop_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to this shop"
                )
        
        return shop
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching shop: {str(e)}"
        )


@router.put("/{shop_id}", response_model=Shop)
def update_shop(
    *,
    db: Session = Depends(get_db),
    shop_id: str,
    shop_in: ShopUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """
    Update a shop. Permissions:
    - SUPER_ADMIN/PLATFORM_ADMIN: Can update any shop
    - SHOP_OWNER: Can update owned shops
    - ADMIN: Can update current shop
    - Others: Not allowed
    """
    try:
        shop = crud_shop.get(db, id=shop_id)
        if not shop:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Shop not found"
            )
        
        # Check permissions
        if not UserRole.is_platform_role(current_user.role):
            if current_user.role == UserRole.SHOP_OWNER:
                if shop.owner_id != str(current_user.id):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="You can only update your own shops"
                    )
            elif current_user.role == UserRole.ADMIN:
                if current_user.shop_id != shop_id:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="You can only update your current shop"
                    )
            else:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions to update shop"
                )
        
        shop = crud_shop.update(db, db_obj=shop, obj_in=shop_in)
        return shop
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating shop: {str(e)}"
        )


@router.delete("/{shop_id}")
def delete_shop(
    *,
    db: Session = Depends(get_db),
    shop_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete a shop. Permissions:
    - SUPER_ADMIN/PLATFORM_ADMIN: Can delete any shop
    - SHOP_OWNER: Can delete owned shops
    - Others: Not allowed
    """
    try:
        shop = crud_shop.get(db, id=shop_id)
        if not shop:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Shop not found"
            )
        
        # Check permissions
        if not UserRole.is_platform_role(current_user.role):
            if current_user.role != UserRole.SHOP_OWNER or shop.owner_id != str(current_user.id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only shop owners can delete their shops"
                )
        
        # Check if this shop is anyone's current shop and clear it
        users_with_this_shop = db.query(User).filter(User.shop_id == shop_id).all()
        for user in users_with_this_shop:
            user.shop_id = None
            db.add(user)
        
        crud_shop.remove(db, id=shop_id)
        db.commit()
        
        return {"message": "Shop deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting shop: {str(e)}"
        )


@router.get("/{shop_id}/users", response_model=List[UserShop])
def get_shop_users(
    *,
    shop_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get all users associated with a shop. Permissions:
    - SUPER_ADMIN/PLATFORM_ADMIN: Can view users of any shop
    - SHOP_OWNER/ADMIN: Can view users of their shops
    - Others: Not allowed
    """
    try:
        shop = crud_shop.get(db, id=shop_id)
        if not shop:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Shop not found"
            )
        
        # Check permissions
        if not UserRole.is_platform_role(current_user.role):
            if current_user.role == UserRole.SHOP_OWNER:
                if shop.owner_id != str(current_user.id):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="You can only view users of your own shops"
                    )
            elif current_user.role == UserRole.ADMIN:
                if current_user.shop_id != shop_id:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="You can only view users of your current shop"
                    )
            else:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions to view shop users"
                )
        
        # Get users associated with this shop
        users = db.query(User).filter(User.shop_id == shop_id).all()
        
        # Convert to UserShop format
        user_shops = []
        for user in users:
            user_shops.append(UserShop(
                shop_id=shop.id,
                shop_name=shop.name,
                role=user.role,
                is_current=True,  # Since we're filtering by current shop
                joined_at=user.created_at or user.updated_at  # Fallback for joined_at
            ))
        
        return user_shops
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching shop users: {str(e)}"
        )
