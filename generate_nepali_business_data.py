#!/usr/bin/env python3
"""
Generate realistic Nepali business data for BillSmart API
Creates 6 months of products, bills, and transaction history
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
from decimal import Decimal
import random
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import Product, Customer, Bill, BillItem, UdharoTransaction, Shop
import uuid

# Your specific shop and customer data
SHOP_ID = "3cefec17-8ae5-45eb-81bc-f273284d7f8d"
CUSTOMERS = [
    {"id": "218447ec-7293-4943-bdfd-26d218990265", "name": "samie", "phone": "9800000000"},
    {"id": "35f3af69-d9f8-4c53-8c9d-c206c5503952", "name": "samir dai", "phone": "9844677382"},
    {"id": "555dbe80-cc0d-4f64-9924-92d500148d2e", "name": "Arun vai", "phone": "1234567890"}
]

# Realistic Nepali products with local prices (in NPR)
NEPALI_PRODUCTS = [
    # Grocery Items
    {"name": "Basmati Rice (1kg)", "category": "Grocery", "price": 180, "cost": 150, "unit": "kg", "sku": "RICE001"},
    {"name": "Toor Dal (1kg)", "category": "Grocery", "price": 140, "cost": 120, "unit": "kg", "sku": "DAL001"},
    {"name": "Mustard Oil (1L)", "category": "Grocery", "price": 280, "cost": 250, "unit": "liter", "sku": "OIL001"},
    {"name": "Ghee (500g)", "category": "Grocery", "price": 650, "cost": 580, "unit": "gram", "sku": "GHEE001"},
    {"name": "Sugar (1kg)", "category": "Grocery", "price": 85, "cost": 75, "unit": "kg", "sku": "SUGAR001"},
    {"name": "Salt (1kg)", "category": "Grocery", "price": 25, "cost": 20, "unit": "kg", "sku": "SALT001"},
    {"name": "Aashirbaad Atta (5kg)", "category": "Grocery", "price": 420, "cost": 380, "unit": "kg", "sku": "ATTA001"},
    {"name": "Maggi Noodles", "category": "Snacks", "price": 25, "cost": 20, "unit": "piece", "sku": "NOODLE001"},
    {"name": "Dairy Milk Chocolate", "category": "Snacks", "price": 110, "cost": 95, "unit": "piece", "sku": "CHOC001"},
    {"name": "Parle-G Biscuit", "category": "Snacks", "price": 35, "cost": 28, "unit": "packet", "sku": "BISC001"},
    
    # Beverages
    {"name": "Coca Cola (250ml)", "category": "Beverages", "price": 40, "cost": 32, "unit": "bottle", "sku": "COKE001"},
    {"name": "Real Juice (1L)", "category": "Beverages", "price": 180, "cost": 150, "unit": "liter", "sku": "JUICE001"},
    {"name": "Lipton Tea (250g)", "category": "Beverages", "price": 320, "cost": 280, "unit": "gram", "sku": "TEA001"},
    {"name": "Nescafe Coffee (50g)", "category": "Beverages", "price": 180, "cost": 155, "unit": "gram", "sku": "COFFEE001"},
    {"name": "Red Bull Energy Drink", "category": "Beverages", "price": 150, "cost": 125, "unit": "can", "sku": "ENERGY001"},
    
    # Dairy Products
    {"name": "DDC Milk (1L)", "category": "Dairy", "price": 85, "cost": 75, "unit": "liter", "sku": "MILK001"},
    {"name": "DDC Curd (500g)", "category": "Dairy", "price": 80, "cost": 68, "unit": "gram", "sku": "CURD001"},
    {"name": "Yak Cheese (250g)", "category": "Dairy", "price": 350, "cost": 300, "unit": "gram", "sku": "CHEESE001"},
    {"name": "Paneer (200g)", "category": "Dairy", "price": 120, "cost": 100, "unit": "gram", "sku": "PANEER001"},
    
    # Personal Care
    {"name": "Lux Soap", "category": "Personal Care", "price": 45, "cost": 38, "unit": "piece", "sku": "SOAP001"},
    {"name": "Colgate Toothpaste", "category": "Personal Care", "price": 85, "cost": 72, "unit": "tube", "sku": "PASTE001"},
    {"name": "Sunsilk Shampoo (200ml)", "category": "Personal Care", "price": 180, "cost": 155, "unit": "ml", "sku": "SHAM001"},
    {"name": "Nivea Cream (100ml)", "category": "Personal Care", "price": 220, "cost": 190, "unit": "ml", "sku": "CREAM001"},
    {"name": "Dettol Handwash (200ml)", "category": "Personal Care", "price": 95, "cost": 80, "unit": "ml", "sku": "WASH001"},
    
    # Household Items
    {"name": "Vim Dishwash (500ml)", "category": "Household", "price": 85, "cost": 72, "unit": "ml", "sku": "DISH001"},
    {"name": "Surf Excel (1kg)", "category": "Household", "price": 280, "cost": 240, "unit": "kg", "sku": "DETERG001"},
    {"name": "Good Knight Mosquito Coil", "category": "Household", "price": 25, "cost": 20, "unit": "packet", "sku": "COIL001"},
    {"name": "Ariel Washing Powder (1kg)", "category": "Household", "price": 320, "cost": 275, "unit": "kg", "sku": "POWDER001"},
    {"name": "Harpic Toilet Cleaner (500ml)", "category": "Household", "price": 120, "cost": 100, "unit": "ml", "sku": "CLEAN001"},
    
    # Stationery
    {"name": "Copy Khata (200 pages)", "category": "Stationery", "price": 45, "cost": 35, "unit": "piece", "sku": "COPY001"},
    {"name": "Cello Pen (Blue)", "category": "Stationery", "price": 15, "cost": 12, "unit": "piece", "sku": "PEN001"},
    {"name": "Pencil (2B)", "category": "Stationery", "price": 8, "cost": 6, "unit": "piece", "sku": "PENCIL001"},
    {"name": "Fevicol Glue (20ml)", "category": "Stationery", "price": 25, "cost": 20, "unit": "piece", "sku": "GLUE001"},
    
    # Electronics/Mobile Accessories
    {"name": "Mobile Charger (Type-C)", "category": "Electronics", "price": 350, "cost": 280, "unit": "piece", "sku": "CHARGE001"},
    {"name": "Earphones", "category": "Electronics", "price": 450, "cost": 380, "unit": "piece", "sku": "PHONE001"},
    {"name": "Power Bank (10000mAh)", "category": "Electronics", "price": 1800, "cost": 1500, "unit": "piece", "sku": "POWER001"},
    {"name": "Mobile Cover", "category": "Electronics", "price": 150, "cost": 120, "unit": "piece", "sku": "COVER001"},
    
    # Spices
    {"name": "Turmeric Powder (100g)", "category": "Spices", "price": 85, "cost": 70, "unit": "gram", "sku": "SPICE001"},
    {"name": "Red Chili Powder (100g)", "category": "Spices", "price": 120, "cost": 100, "unit": "gram", "sku": "SPICE002"},
    {"name": "Coriander Powder (100g)", "category": "Spices", "price": 95, "cost": 80, "unit": "gram", "sku": "SPICE003"},
    {"name": "Garam Masala (50g)", "category": "Spices", "price": 180, "cost": 150, "unit": "gram", "sku": "SPICE004"},
    {"name": "Cumin Seeds (100g)", "category": "Spices", "price": 240, "cost": 200, "unit": "gram", "sku": "SPICE005"},
]

def create_products(db: Session):
    """Create Nepali products"""
    print("🏪 Creating Nepali products...")
    
    created_count = 0
    for product_data in NEPALI_PRODUCTS:
        # Check if product already exists
        existing = db.query(Product).filter(Product.sku == product_data["sku"]).first()
        if existing:
            continue
            
        product = Product(
            id=str(uuid.uuid4()),
            name=product_data["name"],
            description=f"High quality {product_data['name'].lower()} available at best price",
            price=Decimal(str(product_data["price"])),
            cost_price=Decimal(str(product_data["cost"])),
            stock_quantity=random.randint(20, 100),
            min_stock_level=random.randint(5, 15),
            unit=product_data["unit"],
            category=product_data["category"],
            sku=product_data["sku"],
            shop_id=SHOP_ID,
            created_at=datetime.now() - timedelta(days=random.randint(1, 180)),
            updated_at=datetime.now()
        )
        
        db.add(product)
        created_count += 1
    
    db.commit()
    print(f"✅ Created {created_count} products")

def get_random_products(db: Session, count: int = 5):
    """Get random products for bill generation"""
    products = db.query(Product).filter(Product.shop_id == SHOP_ID).all()
    return random.sample(products, min(count, len(products)))

def create_historical_bills(db: Session):
    """Create 6 months of historical bills and transactions"""
    print("🧾 Creating 6 months of historical bills...")
    
    # Date range: 6 months ago to today
    end_date = datetime.now()
    start_date = end_date - timedelta(days=180)
    
    bills_created = 0
    transactions_created = 0
    
    # Generate bills for each month
    for month_offset in range(6):
        month_start = start_date + timedelta(days=month_offset * 30)
        month_end = month_start + timedelta(days=30)
        
        # Generate 15-25 bills per month
        bills_per_month = random.randint(15, 25)
        
        for _ in range(bills_per_month):
            # Random date within the month
            bill_date = month_start + timedelta(
                days=random.randint(0, (month_end - month_start).days),
                hours=random.randint(8, 20),
                minutes=random.randint(0, 59)
            )
            
            # Random customer (80% existing, 20% cash customer)
            if random.random() < 0.8 and CUSTOMERS:
                customer = random.choice(CUSTOMERS)
                customer_id = customer["id"]
            else:
                customer_id = None  # Cash customer
            
            # Generate bill
            bill_id = str(uuid.uuid4())
            bill_number = f"BILL-{bill_date.strftime('%Y')}-{random.randint(100000, 999999)}"
            
            # Get random products for this bill
            products = get_random_products(db, random.randint(1, 8))
            if not products:
                continue
            
            total_amount = Decimal('0')
            bill_items = []
            
            for product in products:
                quantity = random.randint(1, 5)
                unit_price = product.price
                total_price = unit_price * quantity
                total_amount += total_price
                
                bill_items.append({
                    "product_id": product.id,
                    "quantity": quantity,
                    "unit_price": unit_price,
                    "total_price": total_price
                })
            
            # Determine payment status and amount
            payment_scenarios = [
                {"paid_ratio": 1.0, "status": "paid", "method": "cash"},      # 50% fully paid
                {"paid_ratio": 1.0, "status": "paid", "method": "digital"},   # 20% fully paid digital
                {"paid_ratio": 0.0, "status": "pending", "method": "cash"},   # 15% unpaid (udharo)
                {"paid_ratio": random.uniform(0.3, 0.8), "status": "partial", "method": "cash"}  # 15% partial
            ]
            
            weights = [50, 20, 15, 15]
            scenario = random.choices(payment_scenarios, weights=weights)[0]
            
            paid_amount = total_amount * Decimal(str(scenario["paid_ratio"]))
            remaining_amount = total_amount - paid_amount
            
            # Create bill
            bill = Bill(
                id=bill_id,
                bill_number=bill_number,
                shop_id=SHOP_ID,
                customer_id=customer_id,
                total_amount=total_amount,
                paid_amount=paid_amount,
                payment_method=scenario["method"],
                payment_status=scenario["status"],
                created_at=bill_date,
                updated_at=bill_date
            )
            
            db.add(bill)
            db.flush()
            
            # Create bill items
            for item_data in bill_items:
                bill_item = BillItem(
                    id=str(uuid.uuid4()),
                    bill_id=bill_id,
                    product_id=item_data["product_id"],
                    quantity=item_data["quantity"],
                    unit_price=item_data["unit_price"],
                    total_price=item_data["total_price"],
                    created_at=bill_date
                )
                db.add(bill_item)
            
            # Create udharo transaction if there's remaining amount
            if remaining_amount > 0 and customer_id:
                udharo_transaction = UdharoTransaction(
                    id=str(uuid.uuid4()),
                    customer_id=customer_id,
                    bill_id=bill_id,
                    amount=remaining_amount,
                    transaction_type="credit",
                    description=f"Credit for bill {bill_number}",
                    created_at=bill_date
                )
                db.add(udharo_transaction)
                transactions_created += 1
            
            bills_created += 1
    
    # Generate some payment transactions
    print("💰 Creating payment transactions...")
    
    # Get customers with outstanding balances
    customers_with_balance = db.query(Customer).filter(
        Customer.shop_id == SHOP_ID,
        Customer.udharo_balance > 0
    ).all()
    
    for customer in customers_with_balance:
        # Generate 2-5 payments over the 6 months
        num_payments = random.randint(2, 5)
        
        for _ in range(num_payments):
            payment_date = start_date + timedelta(
                days=random.randint(30, 180),  # Payments come later
                hours=random.randint(9, 18),
                minutes=random.randint(0, 59)
            )
            
            # Payment amount (10% to 100% of current balance)
            max_payment = float(customer.udharo_balance) * 0.8
            payment_amount = random.uniform(50, max_payment) if max_payment > 50 else random.uniform(10, max_payment)
            payment_amount = round(payment_amount, 2)
            
            payment_transaction = UdharoTransaction(
                id=str(uuid.uuid4()),
                customer_id=customer.id,
                bill_id=None,
                amount=Decimal(str(payment_amount)),
                transaction_type="payment",
                description=f"Udharo payment received",
                created_at=payment_date
            )
            db.add(payment_transaction)
            transactions_created += 1
    
    db.commit()
    print(f"✅ Created {bills_created} bills and {transactions_created} transactions")

def update_customer_balances(db: Session):
    """Update customer udharo balances based on transactions"""
    print("🔄 Updating customer balances...")
    
    for customer_data in CUSTOMERS:
        customer = db.query(Customer).filter(Customer.id == customer_data["id"]).first()
        if not customer:
            continue
        
        # Calculate balance from transactions
        transactions = db.query(UdharoTransaction).filter(
            UdharoTransaction.customer_id == customer.id
        ).all()
        
        balance = Decimal('0')
        for transaction in transactions:
            if transaction.transaction_type == "credit":
                balance += transaction.amount
            elif transaction.transaction_type == "payment":
                balance -= transaction.amount
        
        customer.udharo_balance = max(balance, Decimal('0'))
        db.add(customer)
    
    db.commit()
    print("✅ Updated customer balances")

def generate_recent_activity(db: Session):
    """Generate some recent activity for better demo"""
    print("⚡ Generating recent activity...")
    
    # Create a few bills from last week
    for _ in range(5):
        recent_date = datetime.now() - timedelta(days=random.randint(1, 7))
        
        customer = random.choice(CUSTOMERS)
        products = get_random_products(db, random.randint(2, 4))
        if not products:
            continue
        
        bill_id = str(uuid.uuid4())
        bill_number = f"BILL-{recent_date.strftime('%Y')}-{random.randint(100000, 999999)}"
        
        total_amount = Decimal('0')
        for product in products:
            quantity = random.randint(1, 3)
            total_amount += product.price * quantity
        
        # 70% chance of partial payment (creating udharo)
        if random.random() < 0.7:
            paid_amount = total_amount * Decimal(str(random.uniform(0.2, 0.6)))
            remaining = total_amount - paid_amount
            
            bill = Bill(
                id=bill_id,
                bill_number=bill_number,
                shop_id=SHOP_ID,
                customer_id=customer["id"],
                total_amount=total_amount,
                paid_amount=paid_amount,
                payment_method="cash",
                payment_status="partial",
                created_at=recent_date,
                updated_at=recent_date
            )
            db.add(bill)
            
            # Create bill items
            for product in products:
                quantity = random.randint(1, 3)
                bill_item = BillItem(
                    id=str(uuid.uuid4()),
                    bill_id=bill_id,
                    product_id=product.id,
                    quantity=quantity,
                    unit_price=product.price,
                    total_price=product.price * quantity,
                    created_at=recent_date
                )
                db.add(bill_item)
            
            # Create udharo transaction
            udharo_transaction = UdharoTransaction(
                id=str(uuid.uuid4()),
                customer_id=customer["id"],
                bill_id=bill_id,
                amount=remaining,
                transaction_type="credit",
                description=f"Credit for bill {bill_number}",
                created_at=recent_date
            )
            db.add(udharo_transaction)
    
    db.commit()
    print("✅ Generated recent activity")

def main():
    """Main function to generate all data"""
    print("🚀 Generating 6 months of Nepali business data...")
    print("=" * 60)
    
    # Get database session
    db = next(get_db())
    
    try:
        # Step 1: Create products
        create_products(db)
        
        # Step 2: Create historical bills and transactions
        create_historical_bills(db)
        
        # Step 3: Update customer balances
        update_customer_balances(db)
        
        # Step 4: Generate recent activity
        generate_recent_activity(db)
        
        # Final update of balances
        update_customer_balances(db)
        
        print("\n" + "=" * 60)
        print("🎉 Data generation complete!")
        
        # Show summary
        product_count = db.query(Product).filter(Product.shop_id == SHOP_ID).count()
        bill_count = db.query(Bill).filter(Bill.shop_id == SHOP_ID).count()
        transaction_count = db.query(UdharoTransaction).join(Customer).filter(Customer.shop_id == SHOP_ID).count()
        
        print(f"\n📊 Summary for Shop: {SHOP_ID}")
        print(f"   📦 Products: {product_count}")
        print(f"   🧾 Bills: {bill_count}")
        print(f"   💰 Udharo Transactions: {transaction_count}")
        
        # Show customer balances
        print(f"\n👥 Customer Balances:")
        for customer_data in CUSTOMERS:
            customer = db.query(Customer).filter(Customer.id == customer_data["id"]).first()
            if customer:
                print(f"   • {customer.name}: Rs. {float(customer.udharo_balance):.2f}")
        
        print(f"\n🔗 Your shop data is ready!")
        print(f"   Shop ID: {SHOP_ID}")
        print(f"   API Endpoint: http://localhost:8000/api/v1/udharo/summary")
        
    except Exception as e:
        print(f"❌ Error generating data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()
