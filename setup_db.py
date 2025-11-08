from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Create a new engine instance
DATABASE_URL = "postgresql+psycopg2://postgres:root@localhost:5432/postgres"
engine = create_engine(DATABASE_URL, echo=True)

# Import all models so they're registered with Base.metadata
from app.models import user, shop, product, customer, bill
from app.core.database import Base

# Create all tables
Base.metadata.create_all(bind=engine)

print("Database tables created successfully!")

# Create a test user
Session = sessionmaker(bind=engine)
session = Session()

from app.models.user import User
from app.core.security import get_password_hash

# Create test user if it doesn't exist
test_user = User(
    email="newuser@test.com",
    password=get_password_hash("password123"),
    full_name="Test User",
    is_active=True,
    is_verified=True,
    role="shop_owner"
)

try:
    session.add(test_user)
    session.commit()
    print("Test user created successfully!")
except Exception as e:
    session.rollback()
    print(f"Error creating test user: {e}")
finally:
    session.close()
