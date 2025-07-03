"""
Database setup script for BillSmart MySQL
Run this script to create all tables in your MySQL database
"""

from sqlalchemy import create_engine
from app.core.database import Base
from app.models import user, shop, customer, product, bill
from app.core.config import settings

def create_database():
    """Create all database tables"""
    try:
        # Create engine
        engine = create_engine(settings.DATABASE_URL)
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        print("✅ Database tables created successfully!")
        print(f"📊 Connected to: {settings.DATABASE_URL}")
        print("🎯 Tables created:")
        for table_name in Base.metadata.tables.keys():
            print(f"   - {table_name}")
            
    except Exception as e:
        print(f"❌ Error creating database: {e}")
        print("💡 Make sure MySQL is running and the database 'billsmart_db' exists")
        print("💡 Run: CREATE DATABASE billsmart_db; in MySQL first")

if __name__ == "__main__":
    create_database()
