from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from ...core.database import get_db
from ...crud.bill import bill as crud_bill, udharo_transaction as crud_udharo
from ...crud.customer import customer as crud_customer
from ...crud.product import product as crud_product
from ...crud.shop import shop as crud_shop
from ...schemas.bill import (
    Bill, BillCreate, BillUpdate, BillWithDetails,
    UdharoTransaction, UdharoTransactionCreate, UdharoTransactionWithDetails
)
from ...api.deps import get_user_shop, get_current_active_user
from ...models.shop import Shop
from ...utils.error_handlers import handle_api_error
from ...models.user import User

# Create POST endpoint for /bills to create a new bill for current shop
@router.post("")
async def create_bill_current_shop(
    *,
    db: Session = Depends(get_db),
    bill_in: BillCreate,
    shop: Shop = Depends(get_user_shop),
    request: Request
):
    """
    Create new bill with items for the current shop
    """
    try:
        # Log the request body for debugging
        request_body = await request.json()
        print(f"Received bill create request: {request_body}")
        
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
        
        # Set the shop_id for the bill - ensure it's a string
        bill_in.shop_id = str(shop.id)
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
                    customer_id=str(bill.customer_id),
                    bill_id=str(bill.id),
                    amount=remaining_amount,
                    transaction_type='credit',
                    description=f"Credit for bill {bill.bill_number}"
                )
                crud_udharo.create_transaction(db, obj_in=udharo_in)
        
        return bill
    except Exception as e:
        print(f"Error creating bill: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating bill: {str(e)}"
        )
