from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ...core.config import settings
from ...core.database import get_db
from ...core.transaction import write_transaction
from ...crud.shop import shop as crud_shop
from ...crud.user import user as crud_user
from ...crud.user_shop_role import user_shop_role as crud_user_shop_role
from ...modules.subscriptions.service import SubscriptionService
from ...schemas.shop import Shop, ShopCreate, ShopUpdate, ShopWithDetails
from ...schemas.user import UserRole, UserShop
from ...schemas.user_shop_role import UserShopRoleCreate, UserShopRoleUpdate, UserShopRoleInDB
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
            # Non-platform roles fallback to owned shops (or none)
            shops = crud_shop.get_by_owner(db, owner_id=str(current_user.id))
        
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
        shops = crud_shop.get_by_owner(db, owner_id=str(current_user.id))
        if not shops:
            return None
        shop = shops[0]
        
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
        
        return {
            "message": "Current shop pointer is deprecated; selected shop is valid for this user.",
            "shop_id": shop_id,
        }
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

        existing_shops = crud_shop.get_by_owner(db, owner_id=owner_id)
        if len(existing_shops) >= settings.MAX_SHOPS_PER_OWNER:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Shop creation limit reached. Maximum {settings.MAX_SHOPS_PER_OWNER} shops allowed per owner."
            )
        
        trial_shop_in = shop_in.model_copy(
            update={
                "subscription_plan": "trial",
                "subscription_status": "trial",
                "billing_cycle": "monthly",
            }
        )

        with write_transaction(db):
            shop = crud_shop.create_with_owner(
                db, obj_in=trial_shop_in, owner_id=owner_id
            )
            SubscriptionService.create_trial_subscription_for_shop(db, shop.id)
        
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
            elif UserRole.is_shop_role(current_user.role) and shop.owner_id != str(current_user.id):
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
                if shop.owner_id != str(current_user.id):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="You can only update your own shop"
                    )
            else:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions to update shop"
                )
        
        with write_transaction(db):
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
                if shop.owner_id != str(current_user.id):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="You can only view users of your own shop"
                    )
            else:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions to view shop users"
                )
        
        role_links = crud_user_shop_role.get_by_shop(db, shop_id=shop_id)

        # Include owner as default shop_owner if no explicit link exists
        has_owner_role = any(str(link.user_id) == str(shop.owner_id) for link in role_links)
        if not has_owner_role:
            role_links.append(
                type("OwnerRole", (), {
                    "user_id": shop.owner_id,
                    "role": "shop_owner",
                    "is_active": True,
                    "joined_at": shop.created_at,
                })()
            )

        user_shops = []
        for link in role_links:
            user_shops.append(UserShop(
                shop_id=shop.id,
                shop_name=shop.name,
                role=link.role,
                is_current=bool(getattr(link, "is_active", True)),
                joined_at=link.joined_at,
            ))
        
        return user_shops
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching shop users: {str(e)}"
        )


@router.patch("/{shop_id}/users/{user_id}/role", response_model=UserShopRoleInDB)
def upsert_shop_user_role(
    *,
    shop_id: str,
    user_id: str,
    role_update: UserShopRoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    shop = crud_shop.get(db, id=shop_id)
    if not shop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shop not found")

    if not UserRole.is_platform_role(current_user.role) and str(shop.owner_id) != str(current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

    target_user = crud_user.get(db, id=user_id)
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    existing = crud_user_shop_role.get_by_user_and_shop(db, user_id=user_id, shop_id=shop_id)
    if existing:
        return crud_user_shop_role.update(db, db_obj=existing, obj_in=role_update)

    if not role_update.role:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Role is required for new assignment")

    create_payload = UserShopRoleCreate(
        user_id=user_id,
        shop_id=shop_id,
        role=role_update.role,
        is_active=True if role_update.is_active is None else role_update.is_active,
    )
    return crud_user_shop_role.upsert(db, obj_in=create_payload)
