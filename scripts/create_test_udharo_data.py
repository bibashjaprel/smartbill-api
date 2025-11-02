#!/usr/bin/env python3
"""
Create Test Udharo Data

This script creates test customers with udharo balances and transactions
for testing the udharo summary API.
"""

def create_test_udharo_data():
    """Create test customers and udharo transactions"""
    
    try:
        from app.core.database import get_db
        from app.crud.user import user as crud_user
        from app.crud.shop import shop as crud_shop
        from app.crud.customer import customer as crud_customer
        from app.crud.bill import udharo_transaction as crud_udharo
        from app.schemas.customer import CustomerCreate
        from app.schemas.bill import UdharoTransactionCreate
        from decimal import Decimal
        import uuid
        
        print("🏗️  Creating test udharo data...")
        
        db = next(get_db())
        
        # Get first user and shop
        users = crud_user.get_multi(db, limit=1)
        if not users:
            print("❌ No users found. Please create a user first.")
            return
        
        user = users[0]
        shops = crud_shop.get_by_owner(db, owner_id=str(user.id))
        if not shops:
            print("❌ No shops found for user. Please create a shop first.")
            return
        
        shop = shops[0]
        print(f"📍 Using shop: {shop.name if hasattr(shop, 'name') else shop.id}")
        
        # Create test customers with udharo balances
        test_customers = [
            {
                "name": "Samir Dai",
                "email": "samir@example.com",
                "phone": "+977-9841234567",
                "address": "Kathmandu, Nepal",
                "udharo_balance": Decimal("765.00")
            },
            {
                "name": "Rita Aunty",
                "email": "rita@example.com", 
                "phone": "+977-9851234568",
                "address": "Lalitpur, Nepal",
                "udharo_balance": Decimal("450.50")
            },
            {
                "name": "Ram Bahadur",
                "email": "ram@example.com",
                "phone": "+977-9861234569", 
                "address": "Bhaktapur, Nepal",
                "udharo_balance": Decimal("1200.25")
            },
            {
                "name": "Maya Didi",
                "email": "maya@example.com",
                "phone": "+977-9871234570",
                "address": "Pokhara, Nepal", 
                "udharo_balance": Decimal("300.00")
            }
        ]
        
        created_customers = []
        
        for customer_data in test_customers:
            udharo_balance = customer_data.pop("udharo_balance")
            
            # Check if customer already exists
            existing_customers = crud_customer.search_by_name_or_phone(
                db, shop_id=str(shop.id), query=customer_data["name"]
            )
            
            if existing_customers:
                customer = existing_customers[0]
                print(f"📝 Updating existing customer: {customer.name}")
                # Update udharo balance
                customer.udharo_balance = udharo_balance
                db.commit()
                db.refresh(customer)
            else:
                # Create new customer
                customer_create = CustomerCreate(
                    **customer_data,
                    shop_id=str(shop.id),
                    udharo_balance=udharo_balance
                )
                customer = crud_customer.create(db, obj_in=customer_create)
                print(f"✅ Created customer: {customer.name} - Rs{udharo_balance}")
            
            created_customers.append(customer)
        
        # Create test udharo transactions
        print("\n💳 Creating test udharo transactions...")
        
        test_transactions = [
            {
                "customer_id": created_customers[0].id,  # Samir Dai
                "amount": Decimal("150.00"),
                "transaction_type": "payment",
                "description": "Udharo payment received"
            },
            {
                "customer_id": created_customers[0].id,  # Samir Dai  
                "amount": Decimal("915.00"),
                "transaction_type": "credit",
                "description": "Items purchased on credit"
            },
            {
                "customer_id": created_customers[1].id,  # Rita Aunty
                "amount": Decimal("450.50"), 
                "transaction_type": "credit",
                "description": "Grocery items on credit"
            },
            {
                "customer_id": created_customers[2].id,  # Ram Bahadur
                "amount": Decimal("800.00"),
                "transaction_type": "credit", 
                "description": "Hardware items purchased"
            },
            {
                "customer_id": created_customers[2].id,  # Ram Bahadur
                "amount": Decimal("400.25"),
                "transaction_type": "credit",
                "description": "Additional items"
            }
        ]
        
        for transaction_data in test_transactions:
            transaction_create = UdharoTransactionCreate(**transaction_data)
            transaction = crud_udharo.create(db, obj_in=transaction_create)
            print(f"💰 Created transaction: Rs{transaction.amount} - {transaction.transaction_type}")
        
        print("\n✅ Test udharo data created successfully!")
        print("\nSummary:")
        print(f"- Created/Updated {len(created_customers)} customers")
        print(f"- Created {len(test_transactions)} transactions")
        
        total_udharo = sum(Decimal(str(c.udharo_balance)) for c in created_customers)
        print(f"- Total outstanding udharo: Rs{total_udharo}")
        
        print("\n🧪 Now run: python verify_udharo_api.py")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure you're running this from the project directory")
    except Exception as e:
        print(f"❌ Error creating test data: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_test_udharo_data()
