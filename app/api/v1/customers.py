from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from ...core.database import get_db
from ...crud.customer import customer as crud_customer
from ...crud.shop import shop as crud_shop
from ...schemas.customer import Customer, CustomerCreate, CustomerUpdate, CustomerWithDetails
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
