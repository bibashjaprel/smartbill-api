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
        
        # Test with undefined customer ID
        headers = {'Authorization': f'Bearer {token}'}
        test_response = requests.get('http://localhost:8000/api/v1/customers/undefined', headers=headers)
        
        print(f"Test response status: {test_response.status_code}")
        print(f"Test response: {test_response.text}")
        
        if test_response.status_code == 400:
            print("✓ Validation working - 400 Bad Request returned for 'undefined' ID")
        elif test_response.status_code == 404:
            print("✗ Still getting 404 - validation not working")
        else:
            print(f"? Unexpected status code: {test_response.status_code}")
            
    else:
        print(f"✗ Login failed: {response.text}")
        
except Exception as e:
    print(f"Error: {e}")
