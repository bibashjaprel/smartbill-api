from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from decimal import Decimal
from ...core.database import get_db
from ...crud.customer import customer as crud_customer
from ...crud.shop import shop as crud_shop
from ...crud.bill import udharo_transaction as crud_udharo
from ...schemas.customer import Customer, CustomerCreate, CustomerUpdate, CustomerWithDetails
from ...schemas.bill import UdharoTransactionCreate, UdharoTransaction
from ...api.deps import get_user_shop, get_current_active_user
from ...models.shop import Shop
from ...utils.error_handlers import handle_api_error
from ...models.user import User
from ...utils.common import get_user_shop_or_404, validate_resource_id
from ...utils.api import get_customer_or_404, apply_search_filter

router = APIRouter()


@router.get("/customers/", response_model=List[Customer])
def read_customers_current_shop(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    skip: int = 0,
    limit: int = 100,
    search: str = Query(None, description="Search by name or phone")
):
    """
    Retrieve customers for current shop (first shop of the user)
    """
    shop = get_user_shop_or_404(db, current_user)
    
    if search:
        customers = crud_customer.search_by_name_or_phone(
            db, shop_id=str(shop.id), query=search
        )
    else:
        customers = crud_customer.get_by_shop(db, shop_id=str(shop.id))
    
    return customers[skip:skip + limit]


@router.get("/{shop_id}/customers/", response_model=List[Customer])
def read_customers(
    *,
    db: Session = Depends(get_db),
    shop: Shop = Depends(get_user_shop),
    skip: int = 0,
    limit: int = 100,
    search: str = Query(None, description="Search by name or phone")
):
    """
    Retrieve customers for a shop
    """
    if search:
        customers = crud_customer.search_by_name_or_phone(
            db, shop_id=str(shop.id), query=search
        )
    else:
        customers = crud_customer.get_by_shop(db, shop_id=str(shop.id))
    
    return customers[skip:skip + limit]


@router.post("/{shop_id}/customers/", response_model=Customer)
def create_customer(
    *,
    db: Session = Depends(get_db),
    customer_in: CustomerCreate,
    shop: Shop = Depends(get_user_shop)
):
    """
    Create new customer
    """
    customer_in.shop_id = shop.id
    customer = crud_customer.create(db, obj_in=customer_in)
    return customer


@router.post("/customers/", response_model=Customer)
def create_customer_current_shop(
    *,
    db: Session = Depends(get_db),
    customer_in: CustomerCreate,
    current_user: User = Depends(get_current_active_user)
):
    """
    Create new customer for current shop (first shop of the user)
    """
    shop = get_user_shop_or_404(db, current_user)
    customer_in.shop_id = shop.id
    customer = crud_customer.create(db, obj_in=customer_in)
    return customer


@router.get("/{shop_id}/customers/{customer_id}", response_model=Customer)
def read_customer(
    *,
    db: Session = Depends(get_db),
    customer_id: str,
    shop: Shop = Depends(get_user_shop)
):
    """
    Get customer by ID
    """
    validate_resource_id(customer_id, "customer")
    customer = crud_customer.get_by_shop_and_id(
        db, shop_id=str(shop.id), customer_id=customer_id
    )
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    return customer


@router.get("/customers/{customer_id}", response_model=Customer)
def read_customer_current_shop(
    *,
    db: Session = Depends(get_db),
    customer_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Get customer by ID for current shop
    """
    customer = get_customer_or_404(db, current_user, customer_id)
    return customer


@router.put("/{shop_id}/customers/{customer_id}", response_model=Customer)
def update_customer(
    *,
    db: Session = Depends(get_db),
    customer_id: str,
    customer_in: CustomerUpdate,
    shop: Shop = Depends(get_user_shop)
):
    """
    Update a customer
    """
    validate_resource_id(customer_id, "customer")
    customer = crud_customer.get_by_shop_and_id(
        db, shop_id=str(shop.id), customer_id=customer_id
    )
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    customer = crud_customer.update(db, db_obj=customer, obj_in=customer_in)
    return customer


@router.put("/customers/{customer_id}", response_model=Customer)
def update_customer_current_shop(
    *,
    db: Session = Depends(get_db),
    customer_id: str,
    customer_in: CustomerUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """
    Update a customer for current shop
    """
    customer = get_customer_or_404(db, current_user, customer_id)
    customer = crud_customer.update(db, db_obj=customer, obj_in=customer_in)
    return customer


@router.delete("/{shop_id}/customers/{customer_id}")
def delete_customer(
    *,
    db: Session = Depends(get_db),
    customer_id: str,
    shop: Shop = Depends(get_user_shop)
):
    """
    Delete a customer
    """
    validate_resource_id(customer_id, "customer")
    customer = crud_customer.get_by_shop_and_id(
        db, shop_id=str(shop.id), customer_id=customer_id
    )
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    crud_customer.remove(db, id=customer_id)
    return {"message": "Customer deleted successfully"}


@router.delete("/customers/{customer_id}")
def delete_customer_current_shop(
    *,
    db: Session = Depends(get_db),
    customer_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete a customer for current shop
    """
    customer = get_customer_or_404(db, current_user, customer_id)
    crud_customer.remove(db, id=customer_id)
    return {"message": "Customer deleted successfully"}


@router.post("/customers/{customer_id}/udharo", response_model=UdharoTransaction)
def record_udharo_payment(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    customer_id: str,
    payment_data: UdharoTransactionCreate
):
    """
    Record a payment for a customer's udharo (credit) balance
    """
    try:
        customer = get_customer_or_404(db, current_user, customer_id)
        
        # Validate payment amount doesn't exceed current balance
        if payment_data.transaction_type == "payment":
            current_balance = customer.udharo_balance if hasattr(customer, 'udharo_balance') and customer.udharo_balance else Decimal('0.0')
            payment_amount = Decimal(str(payment_data.amount))
            
            if payment_amount > current_balance:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Payment amount (Rs{payment_amount}) cannot exceed current balance (Rs{current_balance})"
                )
        
        # Create the transaction
        payment_data.customer_id = customer_id
        transaction = crud_udharo.create(db, obj_in=payment_data)

        # Update udharo_balance if this is a payment
        if payment_data.transaction_type == "payment":
            payment_amount = Decimal(str(payment_data.amount))
            crud_customer.update_udharo_balance(db, customer_id=customer_id, amount=-payment_amount)
        
        return transaction
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Udharo payment error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error recording udharo payment: {str(e)}"
        )


@router.get("/customers/{customer_id}/udharo", response_model=List[UdharoTransaction])
def get_customer_udharo_history(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    customer_id: str
):
    """
    Get udharo transaction history for a customer
    """
    try:
        customer = get_customer_or_404(db, current_user, customer_id)
        
        # Get transaction history
        transactions = crud_udharo.get_by_customer(db, customer_id=customer_id)
        
        return transactions
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Udharo history error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching udharo history: {str(e)}"
        )
