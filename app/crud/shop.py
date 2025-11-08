from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
from ..models.shop import Shop
from ..schemas.shop import ShopCreate, ShopUpdate
from .base import CRUDBase


class CRUDShop(CRUDBase[Shop, ShopCreate, ShopUpdate]):
    def get_by_owner(self, db: Session, *, owner_id: uuid.UUID) -> List[Shop]:
        return db.query(Shop).filter(Shop.owner_id == owner_id).all()

    def create_with_owner(
        self, db: Session, *, obj_in: ShopCreate, owner_id: uuid.UUID
    ) -> Shop:
        obj_in_data = obj_in.dict()
        # Remove owner_id from data to avoid conflicts, use the provided owner_id parameter
        obj_in_data.pop('owner_id', None)
        db_obj = Shop(**obj_in_data, owner_id=owner_id)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_by_owner_and_id(
        self, db: Session, *, owner_id: uuid.UUID, shop_id: uuid.UUID
    ) -> Optional[Shop]:
        return (
            db.query(Shop)
            .filter(Shop.owner_id == owner_id, Shop.id == shop_id)
            .first()
        )


shop = CRUDShop(Shop)
