from sqlalchemy.orm import Session
from typing import List, Optional
from decimal import Decimal
from ..models.customer import Customer
from ..schemas.customer import CustomerCreate, CustomerUpdate
from .base import CRUDBase


class CRUDCustomer(CRUDBase[Customer, CustomerCreate, CustomerUpdate]):
    def get_by_shop(self, db: Session, *, shop_id: str) -> List[Customer]:
        return db.query(Customer).filter(Customer.shop_id == shop_id).all()

    def get_by_shop_and_id(
        self, db: Session, *, shop_id: str, customer_id: str
    ) -> Optional[Customer]:
        return (
            db.query(Customer)
            .filter(Customer.shop_id == shop_id, Customer.id == customer_id)
            .first()
        )

    def search_by_name_or_phone(
        self, db: Session, *, shop_id: str, query: str
    ) -> List[Customer]:
        return (
            db.query(Customer)
            .filter(
                Customer.shop_id == shop_id,
                (Customer.name.ilike(f"%{query}%") | Customer.phone.ilike(f"%{query}%"))
            )
            .all()
        )

    def update_udharo_balance(
        self, db: Session, *, customer_id: str, amount: Decimal
    ) -> Optional[Customer]:
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if customer:
            customer.udharo_balance += amount
            db.commit()
            db.refresh(customer)
        return customer

    def get_customers_with_outstanding_balance(
        self, db: Session, *, shop_id: str
    ) -> List[Customer]:
        return (
            db.query(Customer)
            .filter(
                Customer.shop_id == shop_id,
                Customer.udharo_balance > 0
            )
            .all()
        )


customer = CRUDCustomer(Customer)
