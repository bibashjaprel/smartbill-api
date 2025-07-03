from sqlalchemy.orm import Session
from typing import List, Optional
from ..models.product import Product
from ..schemas.product import ProductCreate, ProductUpdate
from .base import CRUDBase


class CRUDProduct(CRUDBase[Product, ProductCreate, ProductUpdate]):
    def get_by_shop(self, db: Session, *, shop_id: str) -> List[Product]:
        return db.query(Product).filter(Product.shop_id == shop_id).all()

    def get_by_shop_and_id(
        self, db: Session, *, shop_id: str, product_id: str
    ) -> Optional[Product]:
        return (
            db.query(Product)
            .filter(Product.shop_id == shop_id, Product.id == product_id)
            .first()
        )

    def search_by_name_or_category(
        self, db: Session, *, shop_id: str, query: str
    ) -> List[Product]:
        return (
            db.query(Product)
            .filter(
                Product.shop_id == shop_id,
                (Product.name.ilike(f"%{query}%") | Product.category.ilike(f"%{query}%"))
            )
            .all()
        )

    def get_low_stock_products(
        self, db: Session, *, shop_id: str, threshold: int = 10
    ) -> List[Product]:
        return (
            db.query(Product)
            .filter(
                Product.shop_id == shop_id,
                Product.stock_quantity <= threshold
            )
            .all()
        )

    def update_stock(
        self, db: Session, *, product_id: str, quantity_change: int
    ) -> Optional[Product]:
        product = db.query(Product).filter(Product.id == product_id).first()
        if product:
            product.stock_quantity += quantity_change
            db.commit()
            db.refresh(product)
        return product


product = CRUDProduct(Product)
