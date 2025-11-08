import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.core.database import Base

# Test database URL - use a different database for testing
TEST_DATABASE_URL = settings.DATABASE_URL.replace("/postgres", "/test_billsmart_db")

@pytest.fixture(scope="session")
def engine():
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="session")
def TestingSessionLocal(engine):
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal

@pytest.fixture
def db_session(TestingSessionLocal):
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()
