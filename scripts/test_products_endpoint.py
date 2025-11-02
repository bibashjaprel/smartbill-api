#!/usr/bin/env python3
"""
Test script for products endpoint
"""

import requests
import json

# Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

def test_products_endpoint():
    """Test the products endpoint with authentication"""
    
    print("🧪 Testing Products Endpoint")
    print("=" * 50)
    
    # Step 1: Login to get token
    print("1. Logging in...")
    login_data = {
        "email": "admin@billsmart.com",
        "password": "admin123"
    }
    
    try:
        response = requests.post(f"{API_BASE}/auth/login", json=login_data)
        if response.status_code == 200:
            token = response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            print("✅ Login successful")
        else:
            print(f"❌ Login failed: {response.status_code}")
            print(f"Response: {response.text}")
            return
    except Exception as e:
        print(f"❌ Login error: {e}")
        return
    
    # Step 2: Test products endpoint
    print("\n2. Testing products endpoint...")
    try:
        response = requests.get(f"{API_BASE}/products/", headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            products = response.json()
            print(f"✅ Products retrieved successfully!")
            print(f"Number of products: {len(products)}")
            
            if products:
                print("\nFirst product details:")
                product = products[0]
                print(f"- ID: {product.get('id')}")
                print(f"- Name: {product.get('name')}")
                print(f"- Price: {product.get('price')}")
                print(f"- Stock: {product.get('stock')}")
                print(f"- Current Stock: {product.get('current_stock')}")
                print(f"- Category: {product.get('category')}")
        else:
            print(f"❌ Products endpoint failed: {response.status_code}")
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Products endpoint error: {e}")
    
    # Step 3: Test creating a product
    print("\n3. Testing product creation...")
    product_data = {
        "name": "Test Product",
        "description": "A test product",
        "price": 29.99,
        "cost_price": 20.00,
        "stock_quantity": 50,
        "min_stock_level": 10,
        "category": "Test Category",
        "unit": "piece",
        "sku": "TEST-001"
    }
    
    try:
        response = requests.post(f"{API_BASE}/products/", json=product_data, headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            new_product = response.json()
            print("✅ Product created successfully!")
            print(f"Product ID: {new_product.get('id')}")
            print(f"Stock field: {new_product.get('stock')}")
            print(f"Current Stock field: {new_product.get('current_stock')}")
        else:
            print(f"❌ Product creation failed: {response.status_code}")
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Product creation error: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 Product endpoint testing complete!")

if __name__ == "__main__":
    test_products_endpoint()
