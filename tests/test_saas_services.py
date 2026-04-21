from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401
from app.core.database import Base
from app.models.customer import Customer
from app.models.enums import SubscriptionStatus
from app.models.product import Product
from app.models.shop import Shop
from app.models.subscription import Plan
from app.models.user import User
from app.modules.billing.service import BillingService
from app.modules.credit.service import CreditService
from app.modules.inventory.service import InventoryService
from app.modules.subscriptions.service import SubscriptionService
from app.schemas.credit import CreditPaymentCreate
from app.schemas.inventory import StockMovementCreateV2
from app.schemas.invoice import InvoiceCreate, InvoiceItemCreate, InvoicePaymentCreate
from app.schemas.subscription import SubscriptionCreate


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def seed_shop_context(db_session):
    user = User(email="owner@example.com", password="x", full_name="Owner", role="shop_owner")
    db_session.add(user)
    db_session.flush()

    shop = Shop(name="Test Shop", owner_id=user.id)
    db_session.add(shop)
    db_session.flush()

    customer = Customer(name="Customer 1", shop_id=shop.id)
    db_session.add(customer)
    db_session.flush()

    product = Product(name="Item 1", price=Decimal("100.00"), shop_id=shop.id, stock_quantity=20)
    db_session.add(product)
    db_session.commit()

    return {
        "user": user,
        "shop": shop,
        "customer": customer,
        "product": product,
    }


def test_subscription_feature_access_limits(db_session, seed_shop_context):
    shop = seed_shop_context["shop"]

    plan = Plan(
        name="Starter",
        price=Decimal("1000.00"),
        billing_cycle="monthly",
        features={"max_products": 1, "max_users": 1},
        is_active=True,
    )
    db_session.add(plan)
    db_session.commit()

    now = datetime.now(timezone.utc)
    SubscriptionService.create_subscription(
        db_session,
        shop.id,
        SubscriptionCreate(
            plan_id=plan.id,
            status=SubscriptionStatus.active,
            start_date=now,
            current_period_start=now,
            current_period_end=now + timedelta(days=30),
        ),
    )

    allowed, limit, used, reason = SubscriptionService.check_feature_access(db_session, shop.id, "max_products")

    assert allowed is False
    assert limit == 1
    assert used == 1
    assert "Limit reached" in reason


def test_invoice_payment_status_transitions(db_session, seed_shop_context):
    shop = seed_shop_context["shop"]
    customer = seed_shop_context["customer"]
    product = seed_shop_context["product"]

    invoice = BillingService.create_invoice(
        db_session,
        shop.id,
        InvoiceCreate(
            customer_id=customer.id,
            items=[InvoiceItemCreate(product_id=product.id, quantity=2, price=Decimal("100.00"))],
        ),
    )

    assert invoice.total_amount == Decimal("200.00")
    assert str(invoice.status) == "InvoiceStatus.unpaid"

    updated = BillingService.add_payment(
        db_session,
        invoice,
        InvoicePaymentCreate(amount=Decimal("50.00"), method="cash", paid_at=datetime.now(timezone.utc)),
    )
    assert updated.paid_amount == Decimal("50.00")
    assert str(updated.status) == "InvoiceStatus.partial"

    updated = BillingService.add_payment(
        db_session,
        invoice,
        InvoicePaymentCreate(amount=Decimal("150.00"), method="cash", paid_at=datetime.now(timezone.utc)),
    )
    assert updated.paid_amount == Decimal("200.00")
    assert str(updated.status) == "InvoiceStatus.paid"


def test_invoice_overpayment_is_rejected(db_session, seed_shop_context):
    shop = seed_shop_context["shop"]
    customer = seed_shop_context["customer"]
    product = seed_shop_context["product"]

    invoice = BillingService.create_invoice(
        db_session,
        shop.id,
        InvoiceCreate(
            customer_id=customer.id,
            items=[InvoiceItemCreate(product_id=product.id, quantity=1, price=Decimal("100.00"))],
        ),
    )

    with pytest.raises(ValueError, match="exceeds remaining invoice balance"):
        BillingService.add_payment(
            db_session,
            invoice,
            InvoicePaymentCreate(amount=Decimal("150.00"), method="cash", paid_at=datetime.now(timezone.utc)),
        )


def test_invoice_can_be_created_without_customer_for_walkin(db_session, seed_shop_context):
    shop = seed_shop_context["shop"]
    product = seed_shop_context["product"]

    invoice = BillingService.create_invoice(
        db_session,
        shop.id,
        InvoiceCreate(
            customer_id=None,
            items=[InvoiceItemCreate(product_id=product.id, quantity=1, price=Decimal("100.00"))],
        ),
    )

    assert invoice.customer_id is None
    assert invoice.total_amount == Decimal("100.00")


def test_stock_movement_updates_stock(db_session, seed_shop_context):
    user = seed_shop_context["user"]
    shop = seed_shop_context["shop"]
    product = seed_shop_context["product"]

    movement = InventoryService.create_stock_movement(
        db_session,
        shop.id,
        user.id,
        StockMovementCreateV2(
            product_id=product.id,
            movement_type="sale",
            quantity_change=-3,
            reason="Invoice sale",
            reference_type="invoice",
            reference_id="inv_1",
        ),
    )

    db_session.refresh(product)

    assert movement.quantity_before == 20
    assert movement.quantity_after == 17
    assert product.stock_quantity == 17


def test_credit_module_summary_and_payment(db_session, seed_shop_context):
    shop = seed_shop_context["shop"]
    customer = seed_shop_context["customer"]
    product = seed_shop_context["product"]

    invoice = BillingService.create_invoice(
        db_session,
        shop.id,
        InvoiceCreate(
            customer_id=customer.id,
            items=[InvoiceItemCreate(product_id=product.id, quantity=1, price=Decimal("120.00"))],
        ),
    )

    summary = CreditService.get_customer_summary(db_session, shop.id, customer.id)
    assert summary.total_invoiced == Decimal("120.00")
    assert summary.total_due == Decimal("120.00")
    assert summary.outstanding_invoice_count == 1

    updated_invoice = CreditService.apply_payment(
        db_session,
        shop.id,
        customer.id,
        CreditPaymentCreate(invoice_id=invoice.id, amount=Decimal("20.00"), method="cash"),
    )

    assert updated_invoice.paid_amount == Decimal("20.00")

    summary_after = CreditService.get_customer_summary(db_session, shop.id, customer.id)
    assert summary_after.total_due == Decimal("100.00")


def test_trial_subscription_has_1000_bill_limit(db_session, seed_shop_context):
    shop = seed_shop_context["shop"]

    SubscriptionService.create_trial_subscription_for_shop(db_session, shop.id)

    allowed_before_limit, limit_value, used_before_limit, _ = SubscriptionService.check_feature_access(
        db_session,
        shop.id,
        "max_bills",
        used=999,
    )
    assert allowed_before_limit is True
    assert limit_value == 1000
    assert used_before_limit == 999

    allowed_at_limit, limit_value_at_limit, used_at_limit, reason = SubscriptionService.check_feature_access(
        db_session,
        shop.id,
        "max_bills",
        used=1000,
    )
    assert allowed_at_limit is False
    assert limit_value_at_limit == 1000
    assert used_at_limit == 1000
    assert "Limit reached" in reason
