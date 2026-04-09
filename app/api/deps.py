from typing import Generator, Optional
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from ..core.database import get_db
from ..core.security import verify_token
from ..crud.user import user as crud_user
from ..crud.shop import shop as crud_shop
from ..models.user import User
from ..models.shop import Shop

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
