#!/usr/bin/env python3
"""
Create admin user and test udharo data
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal, engine
from app.models.user import User
from app.models.shop import Shop
from app.models.customer import Customer
from app.models.bill import Bill, BillItem, UdharoTransaction
from app.core.security import get_password_hash
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, text
from decimal import Decimal
import uuid

def create_admin_user():
    """Create admin user if not exists"""
    db = SessionLocal()
    try:
        # Check if admin user exists
        admin_user = db.query(User).filter(User.email == "admin@billsmart.com").first()
        if not admin_user:
            print("Creating admin user...")
            admin_user = User(
                email="admin@billsmart.com",
                hashed_password=get_password_hash("admin123"),
                full_name="Admin User",
                is_active=True,
                is_verified=True,
                role="admin"
            )
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)
            print(f"Admin user created with ID: {admin_user.id}")
        else:
            print(f"Admin user already exists with ID: {admin_user.id}")
        
        return admin_user
    finally:
        db.close()

def check_database_data():
    """Check what data exists in the database"""
    db = SessionLocal()
    try:
        print("\n=== Database Data Check ===")
        
        # Check users
        users = db.query(User).all()
        print(f"Users: {len(users)}")
        for user in users:
            print(f"  - {user.email} (ID: {user.id})")
        
        # Check shops
        shops = db.query(Shop).all()
        print(f"\nShops: {len(shops)}")
        for shop in shops:
            print(f"  - {shop.name} (ID: {shop.id}, Owner: {shop.owner_id})")
        
        # Check customers
        customers = db.query(Customer).all()
        print(f"\nCustomers: {len(customers)}")
        for customer in customers[:5]:  # Show first 5
            print(f"  - {customer.name} (ID: {customer.id}, Balance: {customer.udharo_balance})")
        
        # Check bills
        bills = db.query(Bill).all()
        print(f"\nBills: {len(bills)}")
        for bill in bills[:5]:  # Show first 5
            print(f"  - {bill.bill_number} (Total: {bill.total_amount}, Paid: {bill.paid_amount}, Status: {bill.payment_status})")
        
        # Check udharo transactions
        udharo_transactions = db.query(UdharoTransaction).all()
        print(f"\nUdharo Transactions: {len(udharo_transactions)}")
        for transaction in udharo_transactions[:5]:  # Show first 5
            print(f"  - {transaction.transaction_type} {transaction.amount} for customer {transaction.customer_id}")
        
        # Check customers with outstanding balance
        customers_with_balance = db.query(Customer).filter(Customer.udharo_balance > 0).all()
        print(f"\nCustomers with Outstanding Balance: {len(customers_with_balance)}")
        for customer in customers_with_balance:
            print(f"  - {customer.name}: {customer.udharo_balance}")
        
        return len(customers_with_balance) > 0
        
    finally:
        db.close()

def create_test_udharo_data():
    """Create test udharo data if none exists"""
    db = SessionLocal()
    try:
        # Get admin user and shop
        admin_user = db.query(User).filter(User.email == "admin@billsmart.com").first()
        if not admin_user:
            print("Admin user not found")
            return
        
        shop = db.query(Shop).filter(Shop.owner_id == admin_user.id).first()
        if not shop:
            print("Creating test shop...")
            shop = Shop(
                name="Test Shop",
                owner_id=admin_user.id,
                address="Test Address",
                phone="9876543210"
            )
            db.add(shop)
            db.commit()
            db.refresh(shop)
        
        # Create customers with udharo balance
        customers_with_balance = db.query(Customer).filter(Customer.udharo_balance > 0).all()
        if not customers_with_balance:
            print("Creating test customers with udharo balance...")
            
            # Create customers
            customers = [
                Customer(
                    name="Ram Sharma",
                    phone="9841234567",
                    email="ram@example.com",
                    address="Kathmandu",
                    shop_id=shop.id,
                    udharo_balance=Decimal('2500.00')
                ),
                Customer(
                    name="Sita Devi",
                    phone="9851234567",
                    email="sita@example.com",
                    address="Lalitpur",
                    shop_id=shop.id,
                    udharo_balance=Decimal('1500.00')
                ),
                Customer(
                    name="Hari Bahadur",
                    phone="9861234567",
                    email="hari@example.com",
                    address="Bhaktapur",
                    shop_id=shop.id,
                    udharo_balance=Decimal('3000.00')
                )
            ]
            
            for customer in customers:
                db.add(customer)
            
            db.commit()
            
            # Create udharo transactions for these customers
            print("Creating udharo transactions...")
            for customer in customers:
                # Create a credit transaction
                credit_transaction = UdharoTransaction(
                    customer_id=customer.id,
                    amount=customer.udharo_balance,
                    transaction_type='credit',
                    description=f"Initial credit for {customer.name}"
                )
                db.add(credit_transaction)
            
            db.commit()
            print("Test udharo data created successfully!")
        else:
            print(f"Found {len(customers_with_balance)} customers with outstanding balance")
        
    finally:
        db.close()

if __name__ == "__main__":
    print("Setting up test environment...")
    
    # Create admin user
    admin_user = create_admin_user()
    
    # Check existing data
    has_udharo_data = check_database_data()
    
    # Create test data if needed
    if not has_udharo_data:
        print("\nNo udharo data found. Creating test data...")
        create_test_udharo_data()
        print("\nRechecking database after creating test data...")
        check_database_data()
    else:
        print("\nUdharo data already exists in database.")
