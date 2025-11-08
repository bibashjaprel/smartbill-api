"""
Test product-related endpoints (create, list, update, delete)
"""
from test_config import APIClient, TEST_USER, TEST_PRODUCT, print_response

def test_products_flow():
    """Test the complete product management flow"""
    client = APIClient()
    
    # First login to get authentication token
    print("\n=== Logging in ===")
    login_data = {
        "username": TEST_USER["email"],
        "password": TEST_USER["password"]
    }
    response = client.post("/auth/login", login_data)
    print_response(response)
    
    if response.status_code == 200:
        token = response.json().get("access_token")
        client.set_token(token)
        
        # Test product creation
        print("\n=== Creating Product ===")
        response = client.post("/products", TEST_PRODUCT)
        print_response(response)
        
        if response.status_code == 200:
            product_id = response.json().get("id")
            
            print("\n=== Getting Product List ===")
            response = client.get("/products")
            print_response(response)
            
            print(f"\n=== Getting Single Product (ID: {product_id}) ===")
            response = client.get(f"/products/{product_id}")
            print_response(response)
            
            print("\n=== Updating Product ===")
            update_data = TEST_PRODUCT.copy()
            update_data["price"] = 1099.99
            response = client.put(f"/products/{product_id}", update_data)
            print_response(response)
            
            print("\n=== Deleting Product ===")
            response = client.delete(f"/products/{product_id}")
            print_response(response)

if __name__ == "__main__":
    test_products_flow()