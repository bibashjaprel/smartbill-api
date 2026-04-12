from uuid import UUID

from sqlalchemy.orm import Session

from ...crud.customer import customer as crud_customer
from ...models.customer import Customer
from ...schemas.customer import CustomerCreate, CustomerUpdate


class CustomerService:
    @staticmethod
    def list_by_shop(db: Session, shop_id: UUID, skip: int, limit: int, search: str | None = None):
        if search:
            results = crud_customer.search_by_name_or_phone(db, shop_id=shop_id, query=search)
            return results[skip : skip + limit]
        return crud_customer.get_by_shop(db, shop_id=shop_id)[skip : skip + limit]

    @staticmethod
    def create(db: Session, shop_id: UUID, payload: CustomerCreate) -> Customer:
        payload.shop_id = shop_id
        return crud_customer.create(db, obj_in=payload)

    @staticmethod
    def update(db: Session, customer: Customer, payload: CustomerUpdate) -> Customer:
        return crud_customer.update(db, db_obj=customer, obj_in=payload)
