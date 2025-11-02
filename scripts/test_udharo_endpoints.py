#!/usr/bin/env python3
"""
Test script to check udharo data in the database
"""
import requests
import json
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:8000/api/v1"
ADMIN_EMAIL = "admin@billsmart.com"
ADMIN_PASSWORD = "admin123"

def get_admin_token():
    """Get admin token for authentication"""
    login_data = {
        "username": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    }
    
    response = requests.post(
        f"{API_BASE_URL}/auth/login",
        data=login_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"Login failed: {response.status_code}")
        print(response.text)
        return None

def test_udharo_endpoints():
    """Test udharo endpoints"""
    token = get_admin_token()
    if not token:
        print("Could not get admin token")
        return
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    print("Testing udharo endpoints...")
    
    # Test dashboard udharo endpoint
    print("\n1. Testing /dashboard/udharo")
    response = requests.get(f"{API_BASE_URL}/dashboard/udharo", headers=headers)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
    else:
        print(f"Error: {response.text}")
    
    # Test original udharo summary endpoint
    print("\n2. Testing /udharo/summary")
    response = requests.get(f"{API_BASE_URL}/udharo/summary", headers=headers)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
    else:
        print(f"Error: {response.text}")

    # Test customers endpoint to see if there are any customers
    print("\n3. Testing /customers/")
    response = requests.get(f"{API_BASE_URL}/customers/", headers=headers)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Found {len(data)} customers")
        for customer in data[:3]:  # Show first 3
            print(f"  - {customer.get('name', 'N/A')}: Balance = {customer.get('udharo_balance', 0)}")
    else:
        print(f"Error: {response.text}")

    # Test bills endpoint to see if there are any bills
    print("\n4. Testing /bills/")
    response = requests.get(f"{API_BASE_URL}/bills/", headers=headers)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Found {len(data)} bills")
        for bill in data[:3]:  # Show first 3
            print(f"  - Bill {bill.get('bill_number', 'N/A')}: Total = {bill.get('total_amount', 0)}, Paid = {bill.get('paid_amount', 0)}, Status = {bill.get('payment_status', 'N/A')}")
    else:
        print(f"Error: {response.text}")

if __name__ == "__main__":
    test_udharo_endpoints()
