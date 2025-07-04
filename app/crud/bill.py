from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from decimal import Decimal
from ..models.bill import Bill, BillItem, UdharoTransaction
from ..schemas.bill import BillCreate, BillUpdate, UdharoTransactionCreate
from .base import CRUDBase


class CRUDBill(CRUDBase[Bill, BillCreate, BillUpdate]):
    def get_by_shop(self, db: Session, *, shop_id: str) -> List[Bill]:
        return db.query(Bill).filter(Bill.shop_id == shop_id).all()

    def get_by_shop_and_id(
        self, db: Session, *, shop_id: str, bill_id: str
    ) -> Optional[Bill]:
        return (
            db.query(Bill)
            .filter(Bill.shop_id == shop_id, Bill.id == bill_id)
            .first()
        )

    def get_by_shop_and_id_with_items(
        self, db: Session, *, shop_id: str, bill_id: str
    ) -> Optional[Bill]:
        """Get bill with items and customer details"""
        return (
            db.query(Bill)
            .options(
                joinedload(Bill.bill_items).joinedload(BillItem.product),
                joinedload(Bill.customer)
            )
            .filter(Bill.shop_id == shop_id, Bill.id == bill_id)
            .first()
        )

    def get_by_customer(
        self, db: Session, *, customer_id: str
    ) -> List[Bill]:
        return db.query(Bill).filter(Bill.customer_id == customer_id).all()

    def create_with_items(
        self, db: Session, *, obj_in: BillCreate
    ) -> Bill:
        # Create bill without items first
        bill_data = obj_in.dict(exclude={'items'})
        db_bill = Bill(**bill_data)
        db.add(db_bill)
        db.flush()  # Get the bill ID without committing

        # Create bill items
        for item_data in obj_in.items:
            bill_item = BillItem(
                bill_id=db_bill.id,
                **item_data.dict()
            )
            db.add(bill_item)

        db.commit()
        db.refresh(db_bill)
        return db_bill

    def get_pending_bills(self, db: Session, *, shop_id: str) -> List[Bill]:
        return (
            db.query(Bill)
            .filter(
                Bill.shop_id == shop_id,
                Bill.payment_status == 'pending'
            )
            .all()
        )
        
    def get_total_revenue(self, db: Session, *, shop_id: str) -> Decimal:
        """
        Calculate the total revenue for a shop by summing all paid bills
        """
        try:
            from sqlalchemy import func
            result = db.query(func.sum(Bill.total_amount)).filter(
                Bill.shop_id == shop_id,
                Bill.payment_status == 'paid'
            ).scalar()
            return result or Decimal('0.0')
        except Exception as e:
            print(f"Error in get_total_revenue: {str(e)}")
            return Decimal('0.0')
    
    def get_recent_bills(self, db: Session, *, shop_id: str, limit: int = 5) -> List[Bill]:
        """
        Get the most recent bills for a shop
        """
        try:
            return (
                db.query(Bill)
                .filter(Bill.shop_id == shop_id)
                .order_by(Bill.created_at.desc())
                .limit(limit)
                .all()
            )
        except Exception as e:
            print(f"Error in get_recent_bills: {str(e)}")
            return []


class CRUDUdharoTransaction(CRUDBase[UdharoTransaction, UdharoTransactionCreate, None]):
    def get_by_customer(
        self, db: Session, *, customer_id: str
    ) -> List[UdharoTransaction]:
        return (
            db.query(UdharoTransaction)
            .filter(UdharoTransaction.customer_id == customer_id)
            .order_by(UdharoTransaction.created_at.desc())
            .all()
        )

    def create_transaction(
        self, db: Session, *, obj_in: UdharoTransactionCreate
    ) -> UdharoTransaction:
        # Create the transaction
        db_transaction = UdharoTransaction(**obj_in.dict())
        db.add(db_transaction)

        # Update customer's udharo balance
        from ..crud.customer import customer as crud_customer
        if obj_in.transaction_type == 'credit':
            crud_customer.update_udharo_balance(
                db, customer_id=obj_in.customer_id, amount=obj_in.amount
            )
        elif obj_in.transaction_type == 'payment':
            crud_customer.update_udharo_balance(
                db, customer_id=obj_in.customer_id, amount=-obj_in.amount
            )

        db.commit()
        db.refresh(db_transaction)
        return db_transaction


bill = CRUDBill(Bill)
udharo_transaction = CRUDUdharoTransaction(UdharoTransaction)
