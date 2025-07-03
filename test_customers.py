#!/usr/bin/env python3
import requests
import json

# Login to get token
login_data = {
    'username': 'admin@example.com',
    'password': 'admin123'
}

try:
    # Login
    response = requests.post('http://localhost:8000/api/v1/auth/login', data=login_data)
    if response.status_code == 200:
        token_data = response.json()
        token = token_data['access_token']
        print(f"✓ Login successful")
        
        # Test create customer endpoint
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
        customer_data = {
            'name': 'Test Customer',
            'phone': '+1234567890',
            'email': 'test@example.com',
            'address': '123 Test Street'
        }
        
        create_response = requests.post(
            'http://localhost:8000/api/v1/customers/', 
            headers=headers,
            json=customer_data
        )
        
        print(f"Create customer status: {create_response.status_code}")
        if create_response.status_code == 200:
            customer = create_response.json()
            print(f"✓ Customer created successfully")
            print(f"Customer ID: {customer['id']}")
            print(f"Customer Name: {customer['name']}")
            print(f"Customer Phone: {customer['phone']}")
        else:
            print(f"✗ Create customer error: {create_response.text}")
            
        # Test get customers endpoint
        get_response = requests.get('http://localhost:8000/api/v1/customers/', headers=headers)
        print(f"Get customers status: {get_response.status_code}")
        if get_response.status_code == 200:
            customers = get_response.json()
            print(f"✓ Found {len(customers)} customers")
        else:
            print(f"✗ Get customers error: {get_response.text}")
            
    else:
        print(f"✗ Login failed: {response.text}")
        
except Exception as e:
    print(f"Error: {e}")
