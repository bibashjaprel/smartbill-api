import uuid
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api.v1 import reports
from app.core.database import Base
from app.models.customer import Customer
from app.models.invoice import Invoice, InvoiceItem
from app.models.product import Product
from app.models.shop import Shop
from app.models.user import User
from app.schemas.user import UserRole


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)

    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def _seed_shops_and_bills(session):
    owner_1 = User(
        id=uuid.uuid4(),
        email="owner1@example.com",
        full_name="Owner One",
        password="hashed",
        role=UserRole.SHOP_OWNER,
    )
    owner_2 = User(
        id=uuid.uuid4(),
        email="owner2@example.com",
        full_name="Owner Two",
        password="hashed",
        role=UserRole.SHOP_OWNER,
    )
    session.add_all([owner_1, owner_2])
    session.flush()

    shop_1 = Shop(id=uuid.uuid4(), name="Shop One", owner_id=owner_1.id)
    shop_2 = Shop(id=uuid.uuid4(), name="Shop Two", owner_id=owner_2.id)
    shop_3 = Shop(id=uuid.uuid4(), name="Shop Empty", owner_id=owner_1.id)
    session.add_all([shop_1, shop_2, shop_3])
    session.flush()

    customer_1 = Customer(id=uuid.uuid4(), name="Customer One", shop_id=shop_1.id)
    customer_2 = Customer(id=uuid.uuid4(), name="Customer Two", shop_id=shop_2.id)
    session.add_all([customer_1, customer_2])
    session.flush()

    product_1 = Product(
        id=uuid.uuid4(),
        name="Jira Rice",
        price=100,
        cost_price=50,
        stock_quantity=10,
        shop_id=shop_1.id,
    )
    product_2 = Product(
        id=uuid.uuid4(),
        name="Masala",
        price=999,
        cost_price=100,
        stock_quantity=10,
        shop_id=shop_2.id,
    )
    session.add_all([product_1, product_2])
    session.flush()

    bill_1 = Invoice(
        id=uuid.uuid4(),
        shop_id=shop_1.id,
        customer_id=customer_1.id,
        total_amount=200,
        paid_amount=0,
    )
    bill_2 = Invoice(
        id=uuid.uuid4(),
        shop_id=shop_2.id,
        customer_id=customer_2.id,
        total_amount=999,
        paid_amount=0,
    )
    session.add_all([bill_1, bill_2])
    session.flush()

    item_1 = InvoiceItem(
        id=uuid.uuid4(),
        invoice_id=bill_1.id,
        product_id=product_1.id,
        quantity=2,
        price=100,
    )
    item_2 = InvoiceItem(
        id=uuid.uuid4(),
        invoice_id=bill_2.id,
        product_id=product_2.id,
        quantity=1,
        price=999,
    )
    session.add_all([item_1, item_2])
    session.commit()

    return {
        "owner_1": owner_1,
        "owner_2": owner_2,
        "shop_1": shop_1,
        "shop_2": shop_2,
        "shop_3": shop_3,
    }


def test_calculate_summary_and_top_products_are_shop_scoped(db_session):
    seeded = _seed_shops_and_bills(db_session)

    summary = reports._calculate_summary(db_session, seeded["shop_1"].id)
    assert summary["total_revenue"] == 200
    assert summary["total_cost"] == 100
    assert summary["total_profit"] == 100
    assert summary["total_orders"] == 1
    assert summary["avg_order_value"] == 200

    products = reports._calculate_top_products(db_session, seeded["shop_1"].id, limit=10)
    assert products == [
        {
            "product_name": "Jira Rice",
            "total_quantity": 2,
            "total_revenue": 200.0,
        }
    ]


def test_new_shop_with_no_bills_returns_zeros_and_empty_arrays(db_session):
    seeded = _seed_shops_and_bills(db_session)

    summary = reports._calculate_summary(db_session, seeded["shop_3"].id)
    assert summary == {
        "total_revenue": 0,
        "total_cost": 0.0,
        "total_profit": 0.0,
        "total_orders": 0,
        "avg_order_value": 0,
    }

    products = reports._calculate_top_products(db_session, seeded["shop_3"].id, limit=10)
    assert products == []


def test_missing_or_invalid_shop_id_returns_400(db_session):
    user = SimpleNamespace(id=uuid.uuid4(), role=UserRole.PLATFORM_ADMIN, shop_id=None)

    with pytest.raises(HTTPException) as missing_exc:
        reports.get_monthly_stats(
            shop_id=None,
            month=None,
            from_date=None,
            to_date=None,
            db=db_session,
            current_user=user,
        )
    assert missing_exc.value.status_code == 400

    with pytest.raises(HTTPException) as invalid_exc:
        reports.get_monthly_stats(
            shop_id="not-a-uuid",
            month=None,
            from_date=None,
            to_date=None,
            db=db_session,
            current_user=user,
        )
    assert invalid_exc.value.status_code == 400


def test_unauthorized_shop_access_returns_403(db_session):
    seeded = _seed_shops_and_bills(db_session)
    unauthorized_owner = SimpleNamespace(
        id=seeded["owner_2"].id,
        role=UserRole.SHOP_OWNER,
        shop_id=None,
    )

    with pytest.raises(HTTPException) as exc:
        reports.get_monthly_stats(
            shop_id=str(seeded["shop_1"].id),
            month=None,
            from_date=None,
            to_date=None,
            db=db_session,
            current_user=unauthorized_owner,
        )

    assert exc.value.status_code == 403


def test_export_info_shop_id_matches_requested_shop_id(db_session):
    seeded = _seed_shops_and_bills(db_session)
    admin_user = SimpleNamespace(
        id=uuid.uuid4(),
        role=UserRole.PLATFORM_ADMIN,
        shop_id=None,
    )

    response = reports.export_reports(
        shop_id=str(seeded["shop_1"].id),
        type="summary",
        format="json",
        month=None,
        from_date=None,
        to_date=None,
        db=db_session,
        current_user=admin_user,
    )

    assert response["export_info"]["shop_id"] == str(seeded["shop_1"].id)
    assert response["data"]["total_orders"] == 1
