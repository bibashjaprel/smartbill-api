"""
Test authentication endpoints (signup, login, etc.)
"""
import os

import pytest

from tests.test_config import APIClient, TEST_USER, LOGIN_FORM_DATA, print_response


pytestmark = pytest.mark.skipif(
    os.getenv("RUN_LIVE_API_TESTS", "false").lower() not in {"1", "true", "yes", "on"},
    reason="Live API tests are disabled. Set RUN_LIVE_API_TESTS=true to run.",
)

def test_auth_flow():
    """Test the complete authentication flow"""
    client = APIClient()
    
    print("\n=== Testing User Signup ===")
    response = client.post("/auth/signup", TEST_USER)
    print_response(response)
    
    print("\n=== Testing User Login ===")
    # Login uses OAuth2 password flow
    response = client.post(
        "/auth/login", 
        data=LOGIN_FORM_DATA,  # Use form data instead of JSON
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    print_response(response)
    
    if response.status_code == 200:
        # Save token for subsequent requests
        token = response.json().get("access_token")
        client.set_token(token)
        
        print("\n=== Testing Get Current User ===")
        response = client.get("/users/me")
        print_response(response)

if __name__ == "__main__":
    test_auth_flow()
