from typing import Callable, Generator, Optional, Set
from uuid import UUID
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from ..core.database import get_db
from ..core.security import verify_token
from ..crud.user import user as crud_user
from ..crud.shop import shop as crud_shop
from ..models.user import User
from ..models.shop import Shop
from ..models.user_shop_role import UserShopRole
from ..models.enums import ShopRole
from ..modules.subscriptions.service import SubscriptionService

security = HTTPBearer(auto_error=False)


def _normalize_token(raw_token: Optional[str]) -> Optional[str]:
    if not raw_token:
        return None

    token = raw_token.strip().strip('"').strip("'")
    if token.lower().startswith("bearer "):
        token = token[7:].strip()

    return token or None


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
    token: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> User:
    raw_token = token.credentials if token else None

    # Fallback for clients that send a non-standard Authorization header
    # (for example, raw token without "Bearer " prefix).
    if not raw_token:
        raw_token = request.headers.get("authorization")

    if not raw_token:
        raw_token = request.cookies.get("access_token") or request.cookies.get("token")

    normalized_token = _normalize_token(raw_token)
    if not normalized_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    user_id = verify_token(normalized_token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
    
    user = crud_user.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not crud_user.is_active(current_user):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


def get_current_verified_user(
    current_user: User = Depends(get_current_active_user),
) -> User:
    if not crud_user.is_verified(current_user):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email not verified"
        )
    return current_user


def get_current_admin_user(
    current_user: User = Depends(get_current_active_user),
) -> User:
    if not crud_user.is_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Admin access required."
        )
    return current_user


def get_user_shop(
    shop_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Shop:
    shop = crud_shop.get_by_owner_and_id(
        db, owner_id=str(current_user.id), shop_id=shop_id
    )
    if not shop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shop not found or access denied"
        )
    return shop


def get_current_shop(
    shop_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Shop:
    try:
        parsed_shop_id = UUID(shop_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid shop_id")

    shop = crud_shop.get(db, id=parsed_shop_id)
    if not shop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shop not found")

    if shop.owner_id == current_user.id:
        return shop

    role = (
        db.query(UserShopRole)
        .filter(
            UserShopRole.shop_id == parsed_shop_id,
            UserShopRole.user_id == current_user.id,
            UserShopRole.is_active.is_(True),
        )
        .first()
    )
    if not role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied for shop")
    return shop


def require_shop_roles(allowed_roles: Set[ShopRole]) -> Callable:
    def _dependency(
        shop: Shop = Depends(get_current_shop),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user),
    ) -> UserShopRole:
        if shop.owner_id == current_user.id:
            return UserShopRole(user_id=current_user.id, shop_id=shop.id, role=ShopRole.owner)

        role_assignment = (
            db.query(UserShopRole)
            .filter(
                UserShopRole.shop_id == shop.id,
                UserShopRole.user_id == current_user.id,
                UserShopRole.is_active.is_(True),
            )
            .first()
        )
        if not role_assignment:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Missing shop role")

        if role_assignment.role not in allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient shop permissions")

        return role_assignment

    return _dependency


def check_shop_subscription(feature_key: str) -> Callable:
    def _dependency(
        shop: Shop = Depends(get_current_shop),
        db: Session = Depends(get_db),
    ) -> None:
        is_allowed, _, _, reason = SubscriptionService.check_feature_access(db, shop.id, feature_key)
        if not is_allowed:
            raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail=reason or "Subscription limit reached")

    return _dependency
