from sqlalchemy.orm import Session
from typing import List, Optional
from decimal import Decimal
import uuid
from ..models.customer import Customer
from ..schemas.customer import CustomerCreate, CustomerUpdate
from .base import CRUDBase


class CRUDCustomer(CRUDBase[Customer, CustomerCreate, CustomerUpdate]):
    def get_by_shop(self, db: Session, *, shop_id: uuid.UUID) -> List[Customer]:
        return db.query(Customer).filter(Customer.shop_id == shop_id).all()

    def get_by_shop_and_id(
        self, db: Session, *, shop_id: uuid.UUID, customer_id: uuid.UUID
    ) -> Optional[Customer]:
        return (
            db.query(Customer)
            .filter(Customer.shop_id == shop_id, Customer.id == customer_id)
            .first()
        )

    def search_by_name_or_phone(
        self, db: Session, *, shop_id: uuid.UUID, query: str
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
        self, db: Session, *, customer_id: uuid.UUID, amount: Decimal
    ) -> Optional[Customer]:
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if customer:
            customer.udharo_balance += amount
            db.commit()
            db.refresh(customer)
        return customer

    def get_customers_with_outstanding_balance(
        self, db: Session, *, shop_id: uuid.UUID
    ) -> List[Customer]:
        return (
            db.query(Customer)
            .filter(
                Customer.shop_id == shop_id,
                Customer.udharo_balance > 0
            )
            .all()
        )
        
    def get_top_customers(
        self, db: Session, *, shop_id: str, limit: int = 5
    ) -> List[Customer]:
        """
        Get the top customers for a shop based on their purchase amount
        Uses a query to join with bills and calculate total purchases
        """
        try:
            from sqlalchemy import func
            from ..models.invoice import Invoice
            
            # Create a query that sums up the total amount spent by each customer
            result = (
                db.query(
                    Customer,
                    func.sum(Invoice.paid_amount).label('total_spent')
                )
                .join(Invoice, Invoice.customer_id == Customer.id)
                .filter(
                    Customer.shop_id == shop_id,
                    Invoice.paid_amount > 0
                )
                .group_by(Customer.id)
                .order_by(func.sum(Invoice.paid_amount).desc())
                .limit(limit)
                .all()
            )
            
            # Attach the total_spent attribute to each customer object
            for customer, total_spent in result:
                setattr(customer, 'total_spent', total_spent or 0.0)
                
            # Return just the customer objects with the attached total_spent attribute
            return [customer for customer, _ in result]
        except Exception as e:
            print(f"Error in get_top_customers: {str(e)}")
            # If there's an error, return the top customers without spending data
            customers = db.query(Customer).filter(Customer.shop_id == shop_id).limit(limit).all()
            for customer in customers:
                setattr(customer, 'total_spent', 0.0)
            return customers


customer = CRUDCustomer(Customer)
