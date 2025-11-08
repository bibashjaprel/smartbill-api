"""
Initialize database tables and check their status
"""
from sqlalchemy import create_engine, inspect
from app.core.config import settings
from app.core.database import Base

# Import all models to register them
from app.models.user import User
from app.models.shop import Shop
from app.models.product import Product
from app.models.customer import Customer
from app.models.bill import Bill, BillItem, UdharoTransaction

# Create engine with the correct database URL and SQLAlchemy 2.0 settings
engine = create_engine(
    settings.DATABASE_URL,
    echo=True,  # Log SQL queries
    future=True,  # Use SQLAlchemy 2.0 features
    pool_pre_ping=True,  # Check connection before using
    pool_recycle=300,  # Recycle connections every 5 minutes
)

def check_tables():
    """Check if all required tables exist in the database"""
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    print("\nExisting tables in database:", existing_tables)

def initialize_database():
    """Initialize all database tables"""
    print("\nInitializing database tables...")
    try:
        Base.metadata.create_all(bind=engine)
        print("Database tables created successfully!")
    except Exception as e:
        print(f"Error creating database tables: {str(e)}")

if __name__ == "__main__":
    print("=== Database Initialization Script ===")
    print("\nChecking current database state...")
    check_tables()
    
    print("\nInitializing database...")
    initialize_database()
    
    print("\nVerifying database state...")
    check_tables()
