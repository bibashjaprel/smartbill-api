from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ...api.deps import get_current_shop, require_shop_roles
from ...core.database import get_db
from ...crud.customer import customer as crud_customer
from ...models.enums import ShopRole
from ...models.shop import Shop
from ...modules.customers.service import CustomerService
from ...schemas.customer import Customer, CustomerCreate, CustomerUpdate

router = APIRouter()


@router.get("/shops/{shop_id}/customers", response_model=List[Customer])
def list_customers(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=200),
    search: str | None = Query(None),
    db: Session = Depends(get_db),
    shop: Shop = Depends(get_current_shop),
    _role=Depends(require_shop_roles({ShopRole.owner, ShopRole.admin, ShopRole.staff})),
):
    return CustomerService.list_by_shop(db, shop.id, skip, limit, search)


@router.post("/shops/{shop_id}/customers", response_model=Customer)
def create_customer(
    payload: CustomerCreate,
    db: Session = Depends(get_db),
    shop: Shop = Depends(get_current_shop),
    _role=Depends(require_shop_roles({ShopRole.owner, ShopRole.admin})),
):
    return CustomerService.create(db, shop.id, payload)


@router.get("/shops/{shop_id}/customers/{customer_id}", response_model=Customer)
def get_customer(
    customer_id: UUID,
    db: Session = Depends(get_db),
    shop: Shop = Depends(get_current_shop),
    _role=Depends(require_shop_roles({ShopRole.owner, ShopRole.admin, ShopRole.staff})),
):
    customer = crud_customer.get_by_shop_and_id(db, shop_id=shop.id, customer_id=customer_id)
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    return customer


@router.put("/shops/{shop_id}/customers/{customer_id}", response_model=Customer)
def update_customer(
    customer_id: UUID,
    payload: CustomerUpdate,
    db: Session = Depends(get_db),
    shop: Shop = Depends(get_current_shop),
    _role=Depends(require_shop_roles({ShopRole.owner, ShopRole.admin})),
):
    customer = crud_customer.get_by_shop_and_id(db, shop_id=shop.id, customer_id=customer_id)
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    return CustomerService.update(db, customer, payload)


@router.delete("/shops/{shop_id}/customers/{customer_id}")
def delete_customer(
    customer_id: UUID,
    db: Session = Depends(get_db),
    shop: Shop = Depends(get_current_shop),
    _role=Depends(require_shop_roles({ShopRole.owner, ShopRole.admin})),
):
    customer = crud_customer.get_by_shop_and_id(db, shop_id=shop.id, customer_id=customer_id)
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    crud_customer.remove(db, id=customer_id)
    return {"message": "Customer deleted successfully"}
