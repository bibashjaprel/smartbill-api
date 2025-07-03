from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ...core.database import get_db
from ...crud.user import user as crud_user
from ...schemas.user import User, UserUpdate
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
    user = crud_user.update(db, db_obj=current_user, obj_in=user_in)
    return user
