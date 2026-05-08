import uuid
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.api.deps import get_current_shop
from app.core.database import Base, get_db
from app.main import app
from app.models.customer import Customer
from app.models.shop import Shop


def _override_shop_role_dependency(route_path: str) -> None:
    for route in app.routes:
        if getattr(route, "path", "") != route_path:
            continue

        for dependency in route.dependant.dependencies:
            if getattr(dependency.call, "__name__", "") == "_dependency":
                app.dependency_overrides[dependency.call] = lambda: object()


def test_list_customers_returns_paginated_success_response():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    shop_id = uuid.uuid4()
    db = SessionLocal()
    db.add(Customer(name="Walk In", shop_id=shop_id, udharo_balance=Decimal("0.00")))
    db.commit()
    db.close()

    def override_db():
        session = SessionLocal()
        try:
            yield session
        finally:
            session.close()

    def override_shop():
        return Shop(id=shop_id, name="Test Shop", owner_id=uuid.uuid4())

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_shop] = override_shop
    _override_shop_role_dependency("/api/v1/shops/{shop_id}/customers")

    try:
        with TestClient(app) as client:
            response = client.get(f"/api/v1/shops/{shop_id}/customers")
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=engine)

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert payload["data"][0]["name"] == "Walk In"
    assert payload["meta"]["pagination"]["total"] == 1
