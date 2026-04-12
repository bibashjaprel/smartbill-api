from sqlalchemy.orm import Session
from typing import List, Optional

from ..models.user_shop_role import UserShopRole
from ..schemas.user_shop_role import UserShopRoleCreate, UserShopRoleUpdate


class CRUDUserShopRole:
    def get_by_user_and_shop(self, db: Session, *, user_id: str, shop_id: str) -> Optional[UserShopRole]:
        return (
            db.query(UserShopRole)
            .filter(UserShopRole.user_id == user_id, UserShopRole.shop_id == shop_id)
            .first()
        )

    def get_by_shop(self, db: Session, *, shop_id: str) -> List[UserShopRole]:
        return db.query(UserShopRole).filter(UserShopRole.shop_id == shop_id).all()

    def upsert(self, db: Session, *, obj_in: UserShopRoleCreate) -> UserShopRole:
        existing = self.get_by_user_and_shop(db, user_id=str(obj_in.user_id), shop_id=str(obj_in.shop_id))
        if existing:
            existing.role = obj_in.role
            existing.is_active = obj_in.is_active
            db.add(existing)
            db.commit()
            db.refresh(existing)
            return existing

        db_obj = UserShopRole(**obj_in.dict())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(self, db: Session, *, db_obj: UserShopRole, obj_in: UserShopRoleUpdate) -> UserShopRole:
        update_data = obj_in.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_obj, key, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


user_shop_role = CRUDUserShopRole()
