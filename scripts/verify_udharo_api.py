#!/usr/bin/env python3
"""
Comprehensive Udharo API Verification Script

This script will verify:
1. Exact API response structure
2. Data filtering by shop_id
3. Customer udharo balances
4. Authentication and shop association
"""

import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "="*60)
    print(f"📋 {title}")
    print("="*60)

def print_json(data, title="JSON Response"):
    """Pretty print JSON data"""
    print(f"\n{title}:")
    print(json.dumps(data, indent=2, default=str))

def test_udharo_api():
    """Comprehensive test of the udharo API"""
    
    print("🔍 UDHARO API VERIFICATION")
    print("Testing backend API responses and data structure")
    
    # Step 1: Authentication
    print_section("1. AUTHENTICATION TEST")
    
    login_data = {
        "email": "admin@billsmart.com",  # Default admin user
        "password": "admin123"
    }
    
    try:
        print("🔐 Attempting login...")
        response = requests.post(f"{API_BASE}/auth/login", json=login_data)
        print(f"Login Status: {response.status_code}")
        
        if response.status_code == 200:
            auth_data = response.json()
            token = auth_data["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            print("✅ Authentication successful")
            print_json(auth_data, "Auth Response")
        else:
            print(f"❌ Login failed: {response.status_code}")
            print(f"Response: {response.text}")
            return
            
    except Exception as e:
        print(f"❌ Login error: {e}")
        return
    
    # Step 2: User Profile Check
    print_section("2. USER PROFILE & SHOP ASSOCIATION")
    
    try:
        print("👤 Getting user profile...")
        response = requests.get(f"{API_BASE}/users/me", headers=headers)
        print(f"Profile Status: {response.status_code}")
        
        if response.status_code == 200:
            user_data = response.json()
            print("✅ User profile retrieved")
            print_json(user_data, "User Profile")
        else:
            print(f"❌ Profile retrieval failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Profile error: {e}")
    
    # Step 3: Shop Information
    print_section("3. SHOP INFORMATION")
    
    try:
        print("🏪 Getting current shop...")
        response = requests.get(f"{API_BASE}/shops/current", headers=headers)
        print(f"Shop Status: {response.status_code}")
        
        if response.status_code == 200:
            shop_data = response.json()
            print("✅ Shop information retrieved")
            print_json(shop_data, "Shop Data")
            shop_id = shop_data.get("id")
            print(f"📍 Current Shop ID: {shop_id}")
        else:
            print(f"❌ Shop retrieval failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Shop error: {e}")
    
    # Step 4: Customers with Udharo Balances
    print_section("4. CUSTOMERS WITH UDHARO BALANCES")
    
    try:
        print("👥 Getting all customers...")
        response = requests.get(f"{API_BASE}/customers/", headers=headers)
        print(f"Customers Status: {response.status_code}")
        
        if response.status_code == 200:
            customers_data = response.json()
            print(f"✅ Found {len(customers_data)} customers")
            
            # Check for customers with udharo balances
            customers_with_udharo = [
                customer for customer in customers_data 
                if customer.get('udharo_balance', 0) > 0
            ]
            
            print(f"💰 Customers with udharo balance: {len(customers_with_udharo)}")
            
            if customers_with_udharo:
                print("\nCustomers with outstanding balances:")
                for customer in customers_with_udharo:
                    print(f"- {customer.get('name', 'N/A')}: Rs{customer.get('udharo_balance', 0)}")
            else:
                print("ℹ️  No customers found with outstanding udharo balances")
                
            # Show first few customers for debugging
            print_json(customers_data[:3] if customers_data else [], "Sample Customers (first 3)")
            
        else:
            print(f"❌ Customers retrieval failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Customers error: {e}")
    
    # Step 5: MAIN TEST - Udharo Summary
    print_section("5. UDHARO SUMMARY API TEST")
    
    try:
        print("🎯 Testing /api/v1/udharo/summary endpoint...")
        response = requests.get(f"{API_BASE}/udharo/summary", headers=headers)
        print(f"Udharo Summary Status: {response.status_code}")
        
        if response.status_code == 200:
            udharo_data = response.json()
            print("✅ Udharo summary retrieved successfully")
            print_json(udharo_data, "🎯 ACTUAL UDHARO SUMMARY RESPONSE")
            
            # Analyze the response structure
            print("\n📊 RESPONSE ANALYSIS:")
            print(f"- Shop ID: {udharo_data.get('shop', {}).get('id', 'N/A')}")
            print(f"- Shop Name: {udharo_data.get('shop', {}).get('name', 'N/A')}")
            print(f"- Total Outstanding Credit: Rs{udharo_data.get('summary', {}).get('total_outstanding_credit', 0)}")
            print(f"- Customers with Credit: {udharo_data.get('summary', {}).get('customers_with_credit', 0)}")
            print(f"- Customers Listed: {len(udharo_data.get('customers', []))}")
            print(f"- Recent Transactions: {len(udharo_data.get('recent_transactions', []))}")
            
            # Check data types
            print("\n🔍 DATA TYPE VERIFICATION:")
            summary = udharo_data.get('summary', {})
            print(f"- total_outstanding_credit type: {type(summary.get('total_outstanding_credit'))}")
            print(f"- customers_with_credit type: {type(summary.get('customers_with_credit'))}")
            
            if udharo_data.get('customers'):
                first_customer = udharo_data['customers'][0]
                print(f"- customer.udharo_balance type: {type(first_customer.get('udharo_balance'))}")
                
        else:
            print(f"❌ Udharo summary failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Udharo summary error: {e}")
    
    # Step 6: Query Parameters Test
    print_section("6. QUERY PARAMETERS TEST")
    
    try:
        print("🔍 Testing with query parameters...")
        
        # Test with various parameters to see if they're accepted
        test_params = [
            {},  # No parameters
            {"shop_id": "test"},  # Shop ID parameter
            {"limit": "5"},  # Limit parameter
            {"include_zero_balance": "true"}  # Include zero balance
        ]
        
        for i, params in enumerate(test_params):
            print(f"\nTest {i+1}: Parameters = {params}")
            response = requests.get(f"{API_BASE}/udharo/summary", headers=headers, params=params)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                summary = data.get('summary', {})
                print(f"Result: {summary.get('customers_with_credit', 0)} customers, Rs{summary.get('total_outstanding_credit', 0)} total")
            else:
                print(f"Error: {response.text}")
                
    except Exception as e:
        print(f"❌ Query parameters test error: {e}")
    
    # Step 7: Database State Verification
    print_section("7. DATABASE STATE RECOMMENDATIONS")
    
    print("""
📝 BACKEND TEAM VERIFICATION CHECKLIST:

1. DATABASE QUERIES TO RUN:
   ```sql
   -- Check customers with udharo balances
   SELECT id, name, phone, udharo_balance, shop_id 
   FROM customers 
   WHERE udharo_balance > 0;
   
   -- Check udharo transactions
   SELECT id, customer_id, amount, transaction_type, created_at 
   FROM udharo_transactions 
   ORDER BY created_at DESC 
   LIMIT 10;
   
   -- Check shop associations
   SELECT u.email, s.id as shop_id, s.name as shop_name
   FROM users u 
   JOIN shops s ON s.owner_id = u.id;
   ```

2. MANUAL TESTING STEPS:
   - Create test customers with udharo balances
   - Add some udharo transactions
   - Verify shop-user associations
   - Test with different users/shops

3. API ENDPOINT VERIFICATION:
   - Endpoint: GET /api/v1/udharo/summary
   - Authentication: Required (Bearer token)
   - Query Parameters: None required
   - Shop Filtering: Automatic (by JWT token user's shop)
   """)
    
    print_section("8. FRONTEND INTEGRATION GUIDANCE")
    
    print("""
🎯 FOR FRONTEND DEVELOPERS:

1. EXPECTED RESPONSE FORMAT:
   {
     "shop": { "id": "string", "name": "string" },
     "summary": {
       "total_outstanding_credit": number,
       "customers_with_credit": number
     },
     "customers": [
       {
         "id": "string",
         "name": "string", 
         "phone": "string",
         "udharo_balance": number
       }
     ],
     "recent_transactions": [
       {
         "id": "string",
         "customer_id": "string",
         "customer_name": "string",
         "amount": number,
         "transaction_type": "credit"|"payment",
         "created_at": "ISO date string",
         "description": "string"
       }
     ]
   }

2. ERROR HANDLING:
   - 401: Authentication required
   - 404: No shop found for user
   - 500: Server error

3. NETWORK TAB DEBUGGING:
   - Look for: GET /api/v1/udharo/summary
   - Check: Request headers include Authorization
   - Verify: Response status and JSON structure
   """)

if __name__ == "__main__":
    test_udharo_api()
