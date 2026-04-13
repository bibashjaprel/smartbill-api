from typing import List, Optional
from uuid import UUID

from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..models.supplier import Supplier
from ..schemas.supplier import SupplierCreate, SupplierUpdate
from .base import CRUDBase


class CRUDSupplier(CRUDBase[Supplier, SupplierCreate, SupplierUpdate]):
    def get_by_shop(self, db: Session, *, shop_id: UUID, skip: int = 0, limit: int = 100) -> List[Supplier]:
        return (
            db.query(Supplier)
            .filter(Supplier.shop_id == shop_id)
            .order_by(Supplier.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_shop_and_id(self, db: Session, *, shop_id: UUID, supplier_id: UUID) -> Optional[Supplier]:
        return (
            db.query(Supplier)
            .filter(Supplier.shop_id == shop_id, Supplier.id == supplier_id)
            .first()
        )

    def search_by_shop(self, db: Session, *, shop_id: UUID, query: str, skip: int = 0, limit: int = 100) -> List[Supplier]:
        search_term = f"%{query}%"
        return (
            db.query(Supplier)
            .filter(
                Supplier.shop_id == shop_id,
                or_(
                    Supplier.name.ilike(search_term),
                    Supplier.contact_person.ilike(search_term),
                    Supplier.phone.ilike(search_term),
                    Supplier.email.ilike(search_term),
                ),
            )
            .order_by(Supplier.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )


supplier = CRUDSupplier(Supplier)
