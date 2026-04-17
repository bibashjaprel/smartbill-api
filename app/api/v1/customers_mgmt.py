from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from ...api.deps import get_current_shop, require_shop_roles
from ...api.role_sets import SHOP_ROLE_OWNER_ADMIN, SHOP_ROLE_OWNER_ADMIN_STAFF
from ...core.database import get_db
from ...core.transaction import write_transaction
from ...crud.customer import customer as crud_customer
from ...models.enums import ShopRole
from ...models.shop import Shop
from ...modules.customers.service import CustomerService
from ...schemas.customer import Customer, CustomerCreate, CustomerUpdate
from ...utils.api_response import paginated_response, success_response

router = APIRouter()


@router.get("/shops/{shop_id}/customers", response_model=List[Customer])
def list_customers(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=200),
    search: str | None = Query(None),
    db: Session = Depends(get_db),
    shop: Shop = Depends(get_current_shop),
    _role=Depends(require_shop_roles(SHOP_ROLE_OWNER_ADMIN_STAFF)),
):
    items = CustomerService.list_by_shop(db, shop.id, skip, limit, search)
    if search and search.strip():
        total = len(crud_customer.search_by_name_or_phone(db, shop_id=shop.id, query=search.strip()))
    else:
        total = db.query(crud_customer.model).filter(crud_customer.model.shop_id == shop.id).count()
    return paginated_response(
        [Customer.model_validate(row).model_dump(mode="json") for row in items],
        total=total,
        limit=limit,
        skip=skip,
        request_id=getattr(request.state, "request_id", None),
    )


@router.post("/shops/{shop_id}/customers", response_model=Customer)
def create_customer(
    payload: CustomerCreate,
    db: Session = Depends(get_db),
    shop: Shop = Depends(get_current_shop),
    _role=Depends(require_shop_roles(SHOP_ROLE_OWNER_ADMIN)),
):
    with write_transaction(db):
        row = CustomerService.create(db, shop.id, payload)
    return row


@router.get("/shops/{shop_id}/customers/{customer_id}", response_model=Customer)
def get_customer(
    customer_id: UUID,
    db: Session = Depends(get_db),
    shop: Shop = Depends(get_current_shop),
    _role=Depends(require_shop_roles(SHOP_ROLE_OWNER_ADMIN_STAFF)),
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
    _role=Depends(require_shop_roles(SHOP_ROLE_OWNER_ADMIN)),
):
    customer = crud_customer.get_by_shop_and_id(db, shop_id=shop.id, customer_id=customer_id)
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    with write_transaction(db):
        row = CustomerService.update(db, customer, payload)
    return row


@router.delete("/shops/{shop_id}/customers/{customer_id}")
def delete_customer(
    customer_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    shop: Shop = Depends(get_current_shop),
    _role=Depends(require_shop_roles(SHOP_ROLE_OWNER_ADMIN)),
):
    customer = crud_customer.get_by_shop_and_id(db, shop_id=shop.id, customer_id=customer_id)
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    with write_transaction(db):
        crud_customer.remove(db, id=customer_id)
    return success_response(
        {"message": "Customer deleted successfully"},
        request_id=getattr(request.state, "request_id", None),
    )
