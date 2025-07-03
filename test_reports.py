#!/usr/bin/env python3
import requests
import json
from datetime import datetime

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
        
        headers = {'Authorization': f'Bearer {token}'}
        
        # Test monthly trends
        print("\n=== Testing Monthly Trends ===")
        trends_response = requests.get('http://localhost:8000/api/v1/reports/monthly-trends', headers=headers)
        print(f"Monthly trends status: {trends_response.status_code}")
        if trends_response.status_code == 200:
            trends_data = trends_response.json()
            print(f"✓ Monthly trends retrieved: {len(trends_data)} months")
            for month in trends_data:
                print(f"  {month['month']}: Revenue={month['revenue']}, Orders={month['orders']}")
        else:
            print(f"✗ Error: {trends_response.text}")
        
        # Test monthly stats for current month
        print("\n=== Testing Monthly Stats ===")
        current_month = datetime.now().strftime("%Y-%m")
        stats_response = requests.get(f'http://localhost:8000/api/v1/reports/monthly-stats?month={current_month}', headers=headers)
        print(f"Monthly stats status: {stats_response.status_code}")
        if stats_response.status_code == 200:
            stats_data = stats_response.json()
            print(f"✓ Monthly stats for {current_month}:")
            print(f"  Total Revenue: {stats_data['totalRevenue']}")
            print(f"  Total Orders: {stats_data['totalOrders']}")
            print(f"  Avg Order Value: {stats_data['avgOrderValue']}")
        else:
            print(f"✗ Error: {stats_response.text}")
        
        # Test top products
        print("\n=== Testing Top Products ===")
        products_response = requests.get('http://localhost:8000/api/v1/reports/top-products?limit=5', headers=headers)
        print(f"Top products status: {products_response.status_code}")
        if products_response.status_code == 200:
            products_data = products_response.json()
            print(f"✓ Top products retrieved: {len(products_data)} products")
            for product in products_data:
                print(f"  {product['product_name']}: Qty={product['total_quantity']}, Revenue={product['total_revenue']}")
        else:
            print(f"✗ Error: {products_response.text}")
        
        # Test export
        print("\n=== Testing Export ===")
        export_response = requests.get('http://localhost:8000/api/v1/reports/export?type=summary&format=json', headers=headers)
        print(f"Export status: {export_response.status_code}")
        if export_response.status_code == 200:
            export_data = export_response.json()
            print(f"✓ Export successful")
            print(f"  Type: {export_data['export_info']['type']}")
            print(f"  Format: {export_data['export_info']['format']}")
        else:
            print(f"✗ Error: {export_response.text}")
            
    else:
        print(f"✗ Login failed: {response.text}")
        
except Exception as e:
    print(f"Error: {e}")
