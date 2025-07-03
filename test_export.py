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
        
        # Test export endpoint
        headers = {'Authorization': f'Bearer {token}'}
        export_response = requests.get(
            'http://localhost:8000/api/v1/reports/export?month=2025-07&type=sales&format=csv', 
            headers=headers
        )
        
        print(f"Export endpoint status: {export_response.status_code}")
        if export_response.status_code == 200:
            export_data = export_response.json()
            print(f"✓ Export successful")
            print(f"Response: {json.dumps(export_data, indent=2)}")
        else:
            print(f"✗ Export error: {export_response.text}")
            
    else:
        print(f"✗ Login failed: {response.text}")
        
except Exception as e:
    print(f"Error: {e}")
