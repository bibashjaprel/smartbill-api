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
        print(f"✓ Login successful, token: {token[:20]}...")
        
        # Test products endpoint
        headers = {'Authorization': f'Bearer {token}'}
        products_response = requests.get('http://localhost:8000/api/v1/products/', headers=headers)
        
        print(f"Products endpoint status: {products_response.status_code}")
        if products_response.status_code == 200:
            products_data = products_response.json()
            print(f"✓ Products retrieved: {len(products_data)} products")
            if products_data:
                print(f"First product: {products_data[0]['name']}")
        else:
            print(f"✗ Products endpoint error: {products_response.text}")
            
    else:
        print(f"✗ Login failed: {response.text}")
        
except Exception as e:
    print(f"Error: {e}")
