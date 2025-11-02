#!/usr/bin/env python3
"""
Test script for bill endpoint to verify items are included in response
"""
import requests
import json
from decimal import Decimal

# Configuration
BASE_URL = "http://localhost:8000"
BILL_ID = "0010ecbb-d530-4df7-b276-4216dbc5745f"  # The specific bill ID mentioned

def test_bill_endpoint():
    """Test the bill endpoint to ensure items are included"""
    
    # First, get auth token
    print("Getting authentication token...")
    auth_response = requests.post(f"{BASE_URL}/auth/login", json={
        "email": "admin@example.com",
        "password": "admin123"
    })
    
    if auth_response.status_code != 200:
        print(f"Authentication failed: {auth_response.status_code}")
        print(auth_response.text)
        return
    
    token = auth_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    print(f"Authentication successful. Token: {token[:50]}...")
    
    # Test 1: Get bill using /bills/{bill_id} (without shop_id)
    print(f"\nTesting GET /bills/{BILL_ID}")
    response = requests.get(f"{BASE_URL}/api/v1/bills/{BILL_ID}", headers=headers)
    
    print(f"Status code: {response.status_code}")
    if response.status_code == 200:
        bill_data = response.json()
        print(f"Bill found: {bill_data['bill_number']}")
        print(f"Total amount: Rs {bill_data['total_amount']}")
        print(f"Items count: {len(bill_data.get('items', []))}")
        
        if 'items' in bill_data and bill_data['items']:
            print("\nItems in bill:")
            for item in bill_data['items']:
                print(f"  - {item['product_name']}: Qty {item['quantity']} @ Rs {item['unit_price']} = Rs {item['total_price']}")
        else:
            print("⚠️  No items found in bill response!")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
    
    # Test 2: Get current shop first, then test with shop_id
    print(f"\nGetting current shop...")
    shop_response = requests.get(f"{BASE_URL}/api/v1/shops/current", headers=headers)
    
    if shop_response.status_code == 200:
        shop_data = shop_response.json()
        shop_id = shop_data['id']
        print(f"Current shop ID: {shop_id}")
        
        # Test 3: Get bill using /{shop_id}/bills/{bill_id}
        print(f"\nTesting GET /{shop_id}/bills/{BILL_ID}")
        response = requests.get(f"{BASE_URL}/api/v1/{shop_id}/bills/{BILL_ID}", headers=headers)
        
        print(f"Status code: {response.status_code}")
        if response.status_code == 200:
            bill_data = response.json()
            print(f"Bill found: {bill_data['bill_number']}")
            print(f"Total amount: Rs {bill_data['total_amount']}")
            print(f"Items count: {len(bill_data.get('items', []))}")
            
            if 'items' in bill_data and bill_data['items']:
                print("\nItems in bill:")
                for item in bill_data['items']:
                    print(f"  - {item['product_name']}: Qty {item['quantity']} @ Rs {item['unit_price']} = Rs {item['total_price']}")
            else:
                print("⚠️  No items found in bill response!")
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
    else:
        print(f"Failed to get current shop: {shop_response.status_code}")
        print(shop_response.text)
    
    # Test 4: Check if the bill actually exists in database
    print(f"\nChecking if bill exists in database...")
    bills_response = requests.get(f"{BASE_URL}/api/v1/bills/", headers=headers)
    
    if bills_response.status_code == 200:
        bills = bills_response.json()
        matching_bills = [b for b in bills if b['id'] == BILL_ID]
        if matching_bills:
            print(f"Bill {BILL_ID} exists in database")
            print(f"Total amount: Rs {matching_bills[0]['total_amount']}")
        else:
            print(f"Bill {BILL_ID} not found in bills list")
            print(f"Available bills: {len(bills)}")
            if bills:
                print("First few bills:")
                for bill in bills[:3]:
                    print(f"  - {bill['id']}: {bill['bill_number']} - Rs {bill['total_amount']}")
    else:
        print(f"Failed to get bills list: {bills_response.status_code}")

if __name__ == "__main__":
    test_bill_endpoint()
