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
from ...models.user import User

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
    # Get the current user's first shop
    shops = crud_shop.get_by_owner(db, owner_id=str(current_user.id))
    if not shops:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No shops found for the current user"
        )
    shop = shops[0]
    
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
    # Get the current user's first shop
    shops = crud_shop.get_by_owner(db, owner_id=str(current_user.id))
    if not shops:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No shops found for the current user"
        )
    shop = shops[0]
    
    # Set the shop_id for the customer
    customer_in.shop_id = shop.id
    
    # Create the customer
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
    customer = crud_customer.get_by_shop_and_id(
        db, shop_id=str(shop.id), customer_id=customer_id
    )
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
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
    # Validate customer_id parameter
    if not customer_id or customer_id.lower() in ['undefined', 'null', 'none']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid customer ID provided. Customer ID cannot be undefined, null, or empty."
        )
    
    # Get the current user's first shop
    shops = crud_shop.get_by_owner(db, owner_id=str(current_user.id))
    if not shops:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No shops found for the current user"
        )
    shop = shops[0]
    
    customer = crud_customer.get_by_shop_and_id(
        db, shop_id=str(shop.id), customer_id=customer_id
    )
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
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
    # Validate customer_id parameter
    if not customer_id or customer_id.lower() in ['undefined', 'null', 'none']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid customer ID provided. Customer ID cannot be undefined, null, or empty."
        )
    
    # Get the current user's first shop
    shops = crud_shop.get_by_owner(db, owner_id=str(current_user.id))
    if not shops:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No shops found for the current user"
        )
    shop = shops[0]
    
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
    # Validate customer_id parameter
    if not customer_id or customer_id.lower() in ['undefined', 'null', 'none']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid customer ID provided. Customer ID cannot be undefined, null, or empty."
        )
    
    # Get the current user's first shop
    shops = crud_shop.get_by_owner(db, owner_id=str(current_user.id))
    if not shops:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No shops found for the current user"
        )
    shop = shops[0]
    
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
        # Get the current user's first shop
        shops = crud_shop.get_by_owner(db, owner_id=str(current_user.id))
        if not shops:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No shops found for the current user"
            )
        shop = shops[0]
        
        # Verify customer exists and belongs to this shop
        customer = crud_customer.get_by_shop_and_id(
            db, shop_id=str(shop.id), customer_id=customer_id
        )
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found"
            )
        
        # Validate payment amount doesn't exceed current balance
        if payment_data.transaction_type == "payment":
            current_balance = float(customer.udharo_balance) if hasattr(customer, 'udharo_balance') and customer.udharo_balance else 0.0
            payment_amount = float(payment_data.amount)
            
            if payment_amount > current_balance:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Payment amount (Rs{payment_amount}) cannot exceed current balance (Rs{current_balance})"
                )
        
        # Create the transaction
        payment_data.customer_id = customer_id
        transaction = crud_udharo.create(db, obj_in=payment_data)
        
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
        # Get the current user's first shop
        shops = crud_shop.get_by_owner(db, owner_id=str(current_user.id))
        if not shops:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No shops found for the current user"
            )
        shop = shops[0]
        
        # Verify customer exists and belongs to this shop
        customer = crud_customer.get_by_shop_and_id(
            db, shop_id=str(shop.id), customer_id=customer_id
        )
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found"
            )
        
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
