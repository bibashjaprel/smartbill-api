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
        
        # Test dashboard stats endpoint
        headers = {'Authorization': f'Bearer {token}'}
        dashboard_response = requests.get('http://localhost:8000/api/v1/dashboard/stats', headers=headers)
        
        print(f"Dashboard stats status: {dashboard_response.status_code}")
        if dashboard_response.status_code == 200:
            stats_data = dashboard_response.json()
            print(f"✓ Dashboard stats retrieved successfully")
            print(f"Response structure: {json.dumps(stats_data, indent=2)}")
            
            # Validate expected fields
            expected_fields = ['total_products', 'total_customers', 'total_bills', 'total_sales', 'pending_payments', 'low_stock_products']
            missing_fields = [field for field in expected_fields if field not in stats_data]
            
            if missing_fields:
                print(f"✗ Missing fields: {missing_fields}")
            else:
                print(f"✓ All expected fields present")
                print(f"  - Total Products: {stats_data['total_products']}")
                print(f"  - Total Customers: {stats_data['total_customers']}")
                print(f"  - Total Bills: {stats_data['total_bills']}")
                print(f"  - Total Sales: {stats_data['total_sales']}")
                print(f"  - Pending Payments: {stats_data['pending_payments']}")
                print(f"  - Low Stock Products: {stats_data['low_stock_products']}")
        else:
            print(f"✗ Dashboard stats error: {dashboard_response.text}")
            
    else:
        print(f"✗ Login failed: {response.text}")
        
except Exception as e:
    print(f"Error: {e}")
