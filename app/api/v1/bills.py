from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from ...core.database import get_db
from ...crud.bill import bill as crud_bill, udharo_transaction as crud_udharo
from ...crud.customer import customer as crud_customer
from ...crud.product import product as crud_product
from ...schemas.bill import (
    Bill, BillCreate, BillUpdate, BillWithDetails,
    UdharoTransaction, UdharoTransactionCreate, UdharoTransactionWithDetails
)
from ...api.deps import get_user_shop
from ...models.shop import Shop

router = APIRouter()


@router.get("/{shop_id}/bills/", response_model=List[Bill])
def read_bills(
    *,
    db: Session = Depends(get_db),
    shop: Shop = Depends(get_user_shop),
    skip: int = 0,
    limit: int = 100,
    customer_id: str = Query(None, description="Filter by customer ID"),
    status: str = Query(None, description="Filter by payment status")
):
    """
    Retrieve bills for a shop
    """
    if customer_id:
        bills = crud_bill.get_by_customer(db, customer_id=customer_id)
        # Filter by shop to ensure security
        bills = [bill for bill in bills if str(bill.shop_id) == str(shop.id)]
    elif status == 'pending':
        bills = crud_bill.get_pending_bills(db, shop_id=str(shop.id))
    else:
        bills = crud_bill.get_by_shop(db, shop_id=str(shop.id))
    
    return bills[skip:skip + limit]


@router.post("/{shop_id}/bills/", response_model=Bill)
def create_bill(
    *,
    db: Session = Depends(get_db),
    bill_in: BillCreate,
    shop: Shop = Depends(get_user_shop)
):
    """
    Create new bill with items
    """
    # Validate that all products belong to the shop
    for item in bill_in.items:
        product = crud_product.get_by_shop_and_id(
            db, shop_id=str(shop.id), product_id=str(item.product_id)
        )
        if not product:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Product {item.product_id} not found in shop"
            )
        
        # Check if enough stock is available
        if product.stock_quantity < item.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient stock for product {product.name}. Available: {product.stock_quantity}, Requested: {item.quantity}"
            )
    
    # Validate customer if provided
    if bill_in.customer_id:
        customer = crud_customer.get_by_shop_and_id(
            db, shop_id=str(shop.id), customer_id=str(bill_in.customer_id)
        )
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Customer not found in shop"
            )
    
    bill_in.shop_id = shop.id
    bill = crud_bill.create_with_items(db, obj_in=bill_in)
    
    # Update product stock for each item
    for item in bill_in.items:
        crud_product.update_stock(
            db, product_id=str(item.product_id), quantity_change=-item.quantity
        )
    
    # If payment status is pending and customer exists, create udharo transaction
    if bill.payment_status == 'pending' and bill.customer_id:
        remaining_amount = bill.total_amount - bill.paid_amount
        if remaining_amount > 0:
            udharo_in = UdharoTransactionCreate(
                customer_id=bill.customer_id,
                bill_id=bill.id,
                amount=remaining_amount,
                transaction_type='credit',
                description=f"Credit for bill {bill.bill_number}"
            )
            crud_udharo.create_transaction(db, obj_in=udharo_in)
    
    return bill


@router.get("/{shop_id}/bills/{bill_id}", response_model=BillWithDetails)
def read_bill(
    *,
    db: Session = Depends(get_db),
    bill_id: str,
    shop: Shop = Depends(get_user_shop)
):
    """
    Get bill by ID with details
    """
    bill = crud_bill.get_by_shop_and_id(
        db, shop_id=str(shop.id), bill_id=bill_id
    )
    if not bill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bill not found"
        )
    return bill


@router.put("/{shop_id}/bills/{bill_id}", response_model=Bill)
def update_bill(
    *,
    db: Session = Depends(get_db),
    bill_id: str,
    bill_in: BillUpdate,
    shop: Shop = Depends(get_user_shop)
):
    """
    Update a bill (mainly for payment updates)
    """
    bill = crud_bill.get_by_shop_and_id(
        db, shop_id=str(shop.id), bill_id=bill_id
    )
    if not bill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bill not found"
        )
    
    # If updating payment, handle udharo transactions
    if bill_in.paid_amount is not None and bill.customer_id:
        old_remaining = bill.total_amount - bill.paid_amount
        new_remaining = bill.total_amount - bill_in.paid_amount
        payment_difference = bill_in.paid_amount - bill.paid_amount
        
        if payment_difference > 0:
            # Customer made a payment
            udharo_in = UdharoTransactionCreate(
                customer_id=bill.customer_id,
                bill_id=bill.id,
                amount=payment_difference,
                transaction_type='payment',
                description=f"Payment for bill {bill.bill_number}"
            )
            crud_udharo.create_transaction(db, obj_in=udharo_in)
    
    bill = crud_bill.update(db, db_obj=bill, obj_in=bill_in)
    return bill


@router.get("/{shop_id}/customers/{customer_id}/udharo", response_model=List[UdharoTransaction])
def read_customer_udharo(
    *,
    db: Session = Depends(get_db),
    customer_id: str,
    shop: Shop = Depends(get_user_shop)
):
    """
    Get udharo transactions for a customer
    """
    # Verify customer belongs to shop
    customer = crud_customer.get_by_shop_and_id(
        db, shop_id=str(shop.id), customer_id=customer_id
    )
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    
    transactions = crud_udharo.get_by_customer(db, customer_id=customer_id)
    return transactions


@router.post("/{shop_id}/customers/{customer_id}/udharo", response_model=UdharoTransaction)
def create_udharo_transaction(
    *,
    db: Session = Depends(get_db),
    customer_id: str,
    transaction_in: UdharoTransactionCreate,
    shop: Shop = Depends(get_user_shop)
):
    """
    Create a new udharo transaction (manual payment/credit)
    """
    # Verify customer belongs to shop
    customer = crud_customer.get_by_shop_and_id(
        db, shop_id=str(shop.id), customer_id=customer_id
    )
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    
    transaction_in.customer_id = customer.id
    transaction = crud_udharo.create_transaction(db, obj_in=transaction_in)
    return transaction
