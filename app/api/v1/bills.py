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
from ...models.user import User

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
async def create_bill(
    *,
    db: Session = Depends(get_db),
    bill_in: BillCreate,
    shop: Shop = Depends(get_user_shop),
    request: Request
):
    """
    Create new bill with items
    """
    try:
        # Log the request body for debugging
        request_body = await request.json()
        print(f"Received bill create request for specific shop: {request_body}")
        
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


@router.post("/bills/", response_model=Bill)
def create_bill_current_shop(
    *,
    db: Session = Depends(get_db),
    bill_in: BillCreate,
    current_user: User = Depends(get_current_active_user)
):
    """
    Create new bill with items for the current shop (first shop of the user)
    """
    # Get the current user's first shop
    shops = crud_shop.get_by_owner(db, owner_id=str(current_user.id))
    if not shops:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No shops found for the current user"
        )
    shop = shops[0]
    
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


@router.get("/bills/", response_model=List[Bill])
def read_bills_current_shop(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    skip: int = 0,
    limit: int = 100,
    customer_id: str = Query(None, description="Filter by customer ID"),
    status: str = Query(None, description="Filter by payment status")
):
    """
    Retrieve bills for current shop (first shop of the user)
    """
    # Get the current user's first shop
    shops = crud_shop.get_by_owner(db, owner_id=str(current_user.id))
    if not shops:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No shops found for the current user"
        )
    shop = shops[0]
    
    if customer_id:
        bills = crud_bill.get_by_customer(db, customer_id=customer_id)
        # Filter by shop to ensure security
        bills = [bill for bill in bills if str(bill.shop_id) == str(shop.id)]
    elif status == 'pending':
        bills = crud_bill.get_pending_bills(db, shop_id=str(shop.id))
    else:
        bills = crud_bill.get_by_shop(db, shop_id=str(shop.id))
    
    return bills[skip:skip + limit]


@router.get("/bills/{bill_id}", response_model=BillWithDetails)
def read_bill_current_shop(
    *,
    db: Session = Depends(get_db),
    bill_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Get bill by ID with details for current shop
    """
    # Get the current user's first shop
    shops = crud_shop.get_by_owner(db, owner_id=str(current_user.id))
    if not shops:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No shops found for the current user"
        )
    shop = shops[0]
    
    bill = crud_bill.get_by_shop_and_id(
        db, shop_id=str(shop.id), bill_id=bill_id
    )
    if not bill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bill not found"
        )
    return bill


@router.put("/bills/{bill_id}", response_model=Bill)
def update_bill_current_shop(
    *,
    db: Session = Depends(get_db),
    bill_id: str,
    bill_in: BillUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """
    Update a bill for current shop (mainly for payment updates)
    """
    # Get the current user's first shop
    shops = crud_shop.get_by_owner(db, owner_id=str(current_user.id))
    if not shops:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No shops found for the current user"
        )
    shop = shops[0]
    
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


@router.get("/bills/format-example")
def get_bill_format_example():
    """
    Returns an example of the expected format for creating a bill.
    This is for documentation purposes only.
    """
    example = {
        "bill_number": "BILL-001",
        "customer_id": "69854ca1-89d7-4fe9-ae9d-363c5a17685a",  # Optional, can be null
        "total_amount": 1000.50,
        "paid_amount": 500.00,  # Optional, defaults to 0
        "payment_method": "cash",  # Optional, defaults to 'cash'
        "payment_status": "pending",  # Optional, defaults to 'pending'
        "items": [
            {
                "product_id": "49854ca1-89d7-4fe9-ae9d-363c5a17681b",
                "quantity": 2,
                "unit_price": 250.00,
                "total_price": 500.00
            },
            {
                "product_id": "59854ca1-89d7-4fe9-ae9d-363c5a17682c",
                "quantity": 1,
                "unit_price": 500.50,
                "total_price": 500.50
            }
        ]
    }
    return example


@router.post("/bills/debug", include_in_schema=False)
async def debug_bill_request(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Debug endpoint to log the incoming request body for bill creation
    """
    try:
        body = await request.json()
        print("DEBUG - Request Body:", body)
        
        # Validate bill number
        if "bill_number" not in body:
            return {"error": "bill_number is required"}
        
        # Validate total_amount
        if "total_amount" not in body:
            return {"error": "total_amount is required"}
        
        # Validate items
        if "items" not in body or not isinstance(body["items"], list) or len(body["items"]) == 0:
            return {"error": "items must be a non-empty array"}
        
        # Validate each item
        for i, item in enumerate(body["items"]):
            if "product_id" not in item:
                return {"error": f"items[{i}].product_id is required"}
            if "quantity" not in item:
                return {"error": f"items[{i}].quantity is required"}
            if "unit_price" not in item:
                return {"error": f"items[{i}].unit_price is required"}
            if "total_price" not in item:
                return {"error": f"items[{i}].total_price is required"}
        
        return {
            "status": "Request format is valid",
            "received": body
        }
    except Exception as e:
        return {"error": f"Failed to parse request: {str(e)}"}


@router.post("/{shop_id}/bills/verbose", response_model=Bill)
async def create_bill_verbose(
    *,
    shop_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Verbose create bill endpoint with detailed error logging
    """
    try:
        # Get shop
        shop = None
        shops = crud_shop.get_by_owner(db, owner_id=str(current_user.id))
        for s in shops:
            if str(s.id) == shop_id:
                shop = s
                break
        
        if not shop:
            return {"error": f"Shop with ID {shop_id} not found or you don't have access"}
        
        # Parse the request body
        try:
            body = await request.json()
            print(f"Request body: {body}")
        except Exception as e:
            return {"error": f"Failed to parse request body: {str(e)}"}
            
        # Validate required fields
        if "bill_number" not in body:
            return {"error": "bill_number is required"}
        if "total_amount" not in body:
            return {"error": "total_amount is required"}
        if "items" not in body or not isinstance(body["items"], list) or len(body["items"]) == 0:
            return {"error": "items is required and must be a non-empty array"}
            
        # Create a proper BillCreate object
        try:
            from pydantic import ValidationError
            
            # Map fields
            bill_data = {
                "bill_number": body["bill_number"],
                "total_amount": body.get("total_amount"),
                "paid_amount": body.get("paid_amount", 0),
                "payment_method": body.get("payment_method", "cash"),
                "payment_status": body.get("payment_status", "pending"),
                "shop_id": shop_id,
                "items": []
            }
            
            # Add customer_id if provided
            if "customer_id" in body and body["customer_id"]:
                bill_data["customer_id"] = body["customer_id"]
                
            # Process items
            for item in body["items"]:
                bill_data["items"].append({
                    "product_id": item["product_id"],
                    "quantity": item["quantity"],
                    "unit_price": item["unit_price"],
                    "total_price": item["total_price"]
                })
                
            print(f"Parsed bill data: {bill_data}")
            bill_in = BillCreate(**bill_data)
            
        except ValidationError as e:
            return {"error": f"Validation error: {str(e)}"}
        except Exception as e:
            return {"error": f"Error creating BillCreate object: {str(e)}"}
            
        # Now process the bill
        try:
            # Validate that all products belong to the shop
            for item in bill_in.items:
                product = crud_product.get_by_shop_and_id(
                    db, shop_id=str(shop.id), product_id=str(item.product_id)
                )
                if not product:
                    return {"error": f"Product {item.product_id} not found in shop"}
                
                # Check if enough stock is available
                if product.stock_quantity < item.quantity:
                    return {"error": f"Insufficient stock for product {product.name}. Available: {product.stock_quantity}, Requested: {item.quantity}"}
            
            # Validate customer if provided
            if bill_in.customer_id:
                customer = crud_customer.get_by_shop_and_id(
                    db, shop_id=str(shop.id), customer_id=str(bill_in.customer_id)
                )
                if not customer:
                    return {"error": "Customer not found in shop"}
            
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
        except Exception as e:
            db.rollback()
            return {"error": f"Error creating bill: {str(e)}"}
            
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}

from pydantic import ValidationError
