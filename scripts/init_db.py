"""
Initialize database tables and check their status
"""
from sqlalchemy import inspect
from app.core.database import Base, engine

# Import all models to register them
from app.models.user import User
from app.models.shop import Shop
from app.models.product import Product
from app.models.customer import Customer
from app.models.bill import Bill, BillItem, UdharoTransaction

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
