import uuid

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.api.deps import get_current_active_user
from app.core.database import Base, get_db
from app.main import app
from app.models.product import Product
from app.models.shop import Shop
from app.models.user import User
from app.schemas.user import UserRole


def _client_for(user, session_local):
    def override_db():
        session = session_local()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_active_user] = lambda: user
    return TestClient(app)


def test_dashboard_stats_uses_requested_authorized_shop():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    owner = User(id=uuid.uuid4(), email="owner@example.com", full_name="Owner", password="hashed", role=UserRole.SHOP_OWNER)
    first_shop = Shop(id=uuid.uuid4(), name="First shop", owner_id=owner.id)
    selected_shop = Shop(id=uuid.uuid4(), name="Selected shop", owner_id=owner.id)
    db.add_all([owner, first_shop, selected_shop])
    db.add_all([
        Product(name="First product", price=10, stock_quantity=20, shop_id=first_shop.id),
        Product(name="Selected product 1", price=10, stock_quantity=20, shop_id=selected_shop.id),
        Product(name="Selected product 2", price=10, stock_quantity=20, shop_id=selected_shop.id),
    ])
    db.commit()
    selected_shop_id = str(selected_shop.id)
    db.close()

    try:
        with _client_for(owner, SessionLocal) as client:
            response = client.get(f"/api/v1/dashboard/stats?shop_id={selected_shop_id}")
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=engine)

    assert response.status_code == 200
    payload = response.json()
    assert payload["shop"]["id"] == selected_shop_id
    assert payload["total_products"] == 2


def test_dashboard_rejects_an_unauthorized_shop():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    owner = User(id=uuid.uuid4(), email="owner@example.com", full_name="Owner", password="hashed", role=UserRole.SHOP_OWNER)
    other_user = User(id=uuid.uuid4(), email="other@example.com", full_name="Other", password="hashed", role=UserRole.SHOP_OWNER)
    shop = Shop(id=uuid.uuid4(), name="Private shop", owner_id=owner.id)
    db.add_all([owner, other_user, shop])
    db.commit()
    shop_id = str(shop.id)
    db.close()

    try:
        with _client_for(other_user, SessionLocal) as client:
            response = client.get(f"/api/v1/dashboard/stats?shop_id={shop_id}")
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=engine)

    assert response.status_code == 403
