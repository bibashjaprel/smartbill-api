from sqlalchemy.orm import Session
from typing import Optional
from ..models.user import User
from ..schemas.user import UserCreate, UserUpdate
from ..core.security import get_password_hash, verify_password
from .base import CRUDBase


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    def get_by_email(self, db: Session, *, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email).first()

    def get_by_google_id(self, db: Session, *, google_id: str) -> Optional[User]:
        return db.query(User).filter(User.google_id == google_id).first()

    def create(self, db: Session, *, obj_in: UserCreate) -> User:
        db_obj = User(
            email=obj_in.email,
            password_hash=get_password_hash(obj_in.password),
            full_name=obj_in.full_name,
            is_active=obj_in.is_active,
            is_verified=False,  # Email verification required
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def create_google_user(self, db: Session, *, email: str, full_name: str, google_id: str, profile_picture: Optional[str] = None) -> User:
        """Create user from Google OAuth"""
        db_obj = User(
            email=email,
            full_name=full_name,
            google_id=google_id,
            profile_picture=profile_picture,
            is_active=True,
            is_verified=True,  # Google accounts are pre-verified
            password_hash=None,  # No password for OAuth users
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def verify_email(self, db: Session, *, user: User) -> User:
        """Mark user email as verified"""
        user.is_verified = True
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    def update(self, db: Session, *, db_obj: User, obj_in: UserUpdate) -> User:
        update_data = obj_in.dict(exclude_unset=True)
        if "password" in update_data:
            hashed_password = get_password_hash(update_data["password"])
            del update_data["password"]
            update_data["password_hash"] = hashed_password
        return super().update(db, db_obj=db_obj, obj_in=update_data)

    def authenticate(self, db: Session, *, email: str, password: str) -> Optional[User]:
        user = self.get_by_email(db, email=email)
        if not user:
            return None
        if not user.password_hash:  # OAuth user trying to login with password
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user

    def is_active(self, user: User) -> bool:
        return user.is_active

    def is_verified(self, user: User) -> bool:
        return user.is_verified

    def is_admin(self, user: User) -> bool:
        return user.is_admin

    def reset_password(self, db: Session, *, user: User, new_password: str) -> User:
        """Reset user password"""
        user.password_hash = get_password_hash(new_password)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user


user = CRUDUser(User)
