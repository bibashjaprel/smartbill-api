from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from ...core.database import get_db
from ...crud.bill import bill as crud_bill, udharo_transaction as crud_udharo
from ...crud.customer import customer as crud_customer
from ...crud.product import product as crud_product
from ...crud.stock_movement import stock_movement as crud_stock_movement
from ...crud.shop import shop as crud_shop
from ...schemas.bill import (
    Bill, BillCreate, BillUpdate, BillWithDetails,
    UdharoTransaction, UdharoTransactionCreate, UdharoTransactionWithDetails
)
from ...schemas.stock_movement import StockMovementCreate
from ...api.deps import get_user_shop, get_current_active_user
from ...models.shop import Shop
from ...utils.error_handlers import handle_api_error
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
        stock_snapshot = {}
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

            stock_snapshot[str(item.product_id)] = {
                "before": int(product.stock_quantity or 0),
                "cost_price": product.cost_price,
            }
        
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

            before = stock_snapshot[str(item.product_id)]["before"]
            after = before - int(item.quantity)
            movement_payload = StockMovementCreate(
                product_id=item.product_id,
                movement_type="out",
                quantity_change=-int(item.quantity),
                reason=f"Bill {bill.bill_number} stock deduction",
                reference_type="bill",
                reference_id=str(bill.id),
                unit_cost=stock_snapshot[str(item.product_id)]["cost_price"],
            )
            crud_stock_movement.create(
                db,
                shop_id=shop.id,
                actor_user_id=None,
                quantity_before=before,
                quantity_after=after,
                obj_in=movement_payload,
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
    Get bill by ID with details - FIXED to use get_by_shop_and_id_with_items
    """
    bill = crud_bill.get_by_shop_and_id_with_items(
        db, shop_id=str(shop.id), bill_id=bill_id
    )
    if not bill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bill not found"
        )
    
    # Convert to BillWithDetails format
    items = []
    for bill_item in bill.bill_items:
        items.append({
            "id": bill_item.id,
            "bill_id": bill_item.bill_id,
            "product_id": bill_item.product_id,
            "quantity": bill_item.quantity,
            "unit_price": bill_item.unit_price,
            "total_price": bill_item.total_price,
            "created_at": bill_item.created_at,
            "product_name": bill_item.product.name,
            "product_unit": bill_item.product.unit
        })
    
    response_data = {
        "id": bill.id,
        "bill_number": bill.bill_number,
        "customer_id": bill.customer_id,
        "shop_id": bill.shop_id,
        "total_amount": bill.total_amount,
        "paid_amount": bill.paid_amount,
        "payment_method": bill.payment_method,
        "payment_status": bill.payment_status,
        "created_at": bill.created_at,
        "updated_at": bill.updated_at,
        "items": items,
        "customer_name": bill.customer.name if bill.customer else None,
        "remaining_amount": bill.total_amount - bill.paid_amount
    }
    
    return response_data


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
    Create a manual udharo transaction
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
    
    # Ensure the transaction is for the correct customer
    transaction_in.customer_id = customer_id
    
    # If there's a bill_id, validate it belongs to the same customer and shop
    if transaction_in.bill_id:
        bill = crud_bill.get_by_shop_and_id(
            db, shop_id=str(shop.id), bill_id=transaction_in.bill_id
        )
        if not bill or bill.customer_id != customer_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bill not found or doesn't belong to this customer"
            )
    
    transaction = crud_udharo.create_transaction(db, obj_in=transaction_in)
    return transaction


# Routes without shop_id prefix (for general access) - MUST COME FIRST
@router.get("/", response_model=List[Bill])
def read_bills_for_current_shop(
    *,
    db: Session = Depends(get_db),
    shop_id: str = Query(None, description="Shop ID to filter bills (optional)"),
    skip: int = 0,
    limit: int = 100,
    customer_id: str = Query(None, description="Filter by customer ID"),
    status: str = Query(None, description="Filter by payment status"),
    current_user: User = Depends(get_current_active_user)
):
    """
    Retrieve bills with optional shop_id query parameter (for frontend compatibility)
    """
    try:
        # If shop_id is provided, validate it belongs to the current user
        if shop_id:
            user_shops = crud_shop.get_by_owner(db, owner_id=str(current_user.id))
            user_shop_ids = [str(shop.id) for shop in user_shops]
            
            if shop_id not in user_shop_ids:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have access to this shop"
                )
            
            target_shop_id = shop_id
        else:
            # Fall back to current user's first shop
            user_shops = crud_shop.get_by_owner(db, owner_id=str(current_user.id))
            if not user_shops:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No shops found for the current user"
                )
            target_shop_id = str(user_shops[0].id)
        
        # Get bills based on filters
        if customer_id:
            bills = crud_bill.get_by_customer(db, customer_id=customer_id)
            # Filter by shop to ensure security
            bills = [bill for bill in bills if str(bill.shop_id) == target_shop_id]
        elif status == 'pending':
            bills = crud_bill.get_pending_bills(db, shop_id=target_shop_id)
        else:
            bills = crud_bill.get_by_shop(db, shop_id=target_shop_id)
        
        return bills[skip:skip + limit]
        
    except Exception as e:
        print(f"Error fetching bills: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching bills: {str(e)}"
        )


@router.post("/", response_model=Bill)
async def create_bill_for_current_shop(
    *,
    db: Session = Depends(get_db),
    bill_in: BillCreate,
    current_user: User = Depends(get_current_active_user),
    request: Request
):
    """
    Create new bill with items for current shop
    """
    try:
        # Get the current user's first shop
        user_shops = crud_shop.get_by_owner(db, owner_id=str(current_user.id))
        if not user_shops:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No shops found for the current user"
            )
        shop = user_shops[0]
        
        # Log the request body for debugging
        request_body = await request.json()
        print(f"Received bill create request for current shop: {request_body}")
        
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


@router.get("/{bill_id}", response_model=BillWithDetails)
def read_bill_for_current_shop(
    *,
    db: Session = Depends(get_db),
    bill_id: str,
    shop: Shop = Depends(get_user_shop)
):
    """
    Get bill by ID with details for current shop - FIXED to use get_by_shop_and_id_with_items
    """
    bill = crud_bill.get_by_shop_and_id_with_items(
        db, shop_id=str(shop.id), bill_id=bill_id
    )
    if not bill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bill not found"
        )
    
    # Convert to BillWithDetails format
    items = []
    for bill_item in bill.bill_items:
        items.append({
            "id": bill_item.id,
            "bill_id": bill_item.bill_id,
            "product_id": bill_item.product_id,
            "quantity": bill_item.quantity,
            "unit_price": bill_item.unit_price,
            "total_price": bill_item.total_price,
            "created_at": bill_item.created_at,
            "product_name": bill_item.product.name,
            "product_unit": bill_item.product.unit
        })
    
    response_data = {
        "id": bill.id,
        "bill_number": bill.bill_number,
        "customer_id": bill.customer_id,
        "shop_id": bill.shop_id,
        "total_amount": bill.total_amount,
        "paid_amount": bill.paid_amount,
        "payment_method": bill.payment_method,
        "payment_status": bill.payment_status,
        "created_at": bill.created_at,
        "updated_at": bill.updated_at,
        "items": items,
        "customer_name": bill.customer.name if bill.customer else None,
        "remaining_amount": bill.total_amount - bill.paid_amount
    }
    
    return response_data


@router.put("/{bill_id}", response_model=Bill)
def update_bill_for_current_shop(
    *,
    db: Session = Depends(get_db),
    bill_id: str,
    bill_in: BillUpdate,
    shop: Shop = Depends(get_user_shop)
):
    """
    Update a bill for current shop (mainly for payment updates)
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


# Route to handle GET /bills?shop_id=xxx (frontend compatibility)
@router.get("", response_model=List[Bill])
def read_bills_with_shop_query(
    *,
    db: Session = Depends(get_db),
    shop_id: str = Query(None, description="Shop ID to filter bills"),
    skip: int = 0,
    limit: int = 100,
    customer_id: str = Query(None, description="Filter by customer ID"),
    status: str = Query(None, description="Filter by payment status"),
    current_user: User = Depends(get_current_active_user)
):
    """
    Retrieve bills with shop_id as query parameter (for frontend compatibility)
    """
    try:
        # If shop_id is provided, validate it belongs to the current user
        if shop_id:
            user_shops = crud_shop.get_by_owner(db, owner_id=str(current_user.id))
            user_shop_ids = [str(shop.id) for shop in user_shops]
            
            if shop_id not in user_shop_ids:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have access to this shop"
                )
            
            # Use the provided shop_id
            target_shop_id = shop_id
        else:
            # Fall back to current user's first shop
            user_shops = crud_shop.get_by_owner(db, owner_id=str(current_user.id))
            if not user_shops:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No shops found for the current user"
                )
            target_shop_id = str(user_shops[0].id)
        
        # Get bills based on filters
        if customer_id:
            bills = crud_bill.get_by_customer(db, customer_id=customer_id)
            # Filter by shop to ensure security
            bills = [bill for bill in bills if str(bill.shop_id) == target_shop_id]
        elif status == 'pending':
            bills = crud_bill.get_pending_bills(db, shop_id=target_shop_id)
        else:
            bills = crud_bill.get_by_shop(db, shop_id=target_shop_id)
        
        return bills[skip:skip + limit]
        
    except Exception as e:
        print(f"Error fetching bills: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching bills: {str(e)}"
        )


@router.post("", response_model=Bill)
async def create_bill_no_slash(
    *,
    db: Session = Depends(get_db),
    bill_in: BillCreate,
    shop: Shop = Depends(get_user_shop),
    request: Request
):
    """
    Create new bill with items (no trailing slash)
    """
    # Delegate to the main create function
    return await create_bill_for_current_shop(
        db=db, bill_in=bill_in, shop=shop, request=request
    )
