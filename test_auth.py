#!/usr/bin/env python3
"""
Test script for BillSmart API authentication features
"""

import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_registration():
    """Test user registration"""
    print("🧪 Testing user registration...")
    
    # Use a timestamp to make email unique
    import time
    timestamp = str(int(time.time()))
    
    data = {
        "email": f"test{timestamp}@example.com",
        "password": "testpassword123",
        "full_name": "Test User"
    }
    
    response = requests.post(f"{BASE_URL}/auth/register", json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 200:
        print("✅ Registration successful!")
        return True
    elif response.status_code == 400 and "already exists" in response.json().get("detail", ""):
        print("✅ Registration works (user already exists)!")
        return True
    else:
        print("❌ Registration failed!")
        return False

def test_login_without_verification():
    """Test login before email verification"""
    print("\n🧪 Testing login without email verification...")
    
    data = {
        "email": "test@example.com",
        "password": "testpassword123"
    }
    
    response = requests.post(f"{BASE_URL}/auth/login-email", json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 400:
        print("✅ Correctly rejected unverified email!")
        return True
    else:
        print("❌ Should have rejected unverified email!")
        return False

def test_oauth2_login():
    """Test OAuth2 form login"""
    print("\n🧪 Testing OAuth2 form login...")
    
    data = {
        "username": "test@example.com",  # Email in username field
        "password": "testpassword123"
    }
    
    response = requests.post(
        f"{BASE_URL}/auth/login", 
        data=data,  # Form data, not JSON
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 400:
        print("✅ Correctly rejected unverified email!")
        return True
    else:
        print("❌ Should have rejected unverified email!")
        return False

def test_endpoints_exist():
    """Test that all new endpoints exist"""
    print("\n🧪 Testing endpoint availability...")
    
    endpoints = [
        "/auth/register",
        "/auth/login",
        "/auth/login-email", 
        "/auth/google/login",
        "/auth/verify-email",
        "/auth/resend-verification",
        "/auth/forgot-password",
        "/auth/reset-password"
    ]
    
    all_exist = True
    for endpoint in endpoints:
        try:
            response = requests.options(f"{BASE_URL}{endpoint}")
            if response.status_code in [200, 405]:  # 405 = Method Not Allowed is OK
                print(f"✅ {endpoint} - Available")
            else:
                print(f"❌ {endpoint} - Not available ({response.status_code})")
                all_exist = False
        except Exception as e:
            print(f"❌ {endpoint} - Error: {e}")
            all_exist = False
    
    return all_exist

def test_google_auth_endpoint():
    """Test Google auth endpoint with invalid token"""
    print("\n🧪 Testing Google auth endpoint...")
    
    data = {"token": "invalid-token"}
    response = requests.post(f"{BASE_URL}/auth/google/login", json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 400:
        print("✅ Correctly rejected invalid Google token!")
        return True
    else:
        print(f"❌ Expected 400, got {response.status_code}")
        return False


def test_forgot_password():
    """Test forgot password endpoint"""
    print("\n🧪 Testing forgot password endpoint...")
    
    data = {"email": "nonexistent@example.com"}
    response = requests.post(f"{BASE_URL}/auth/forgot-password", json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 200:
        print("✅ Forgot password endpoint working!")
        return True
    else:
        print(f"❌ Expected 200, got {response.status_code}")
        return False


def test_reset_password_invalid_token():
    """Test reset password with invalid token"""
    print("\n🧪 Testing reset password with invalid token...")
    
    data = {
        "token": "invalid-token",
        "new_password": "newpassword123"
    }
    response = requests.post(f"{BASE_URL}/auth/reset-password", json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 400:
        print("✅ Correctly rejected invalid reset token!")
        return True
    else:
        print(f"❌ Expected 400, got {response.status_code}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting BillSmart API Authentication Tests")
    print("=" * 50)
    
    try:
        # Test server connectivity
        response = requests.get(f"{BASE_URL.replace('/api/v1', '')}/health")
        if response.status_code != 200:
            print("❌ Server is not running! Please start the server first.")
            return
        print("✅ Server is running!")
        
        # Run tests
        tests = [
            test_endpoints_exist,
            test_registration,
            test_login_without_verification,
            test_oauth2_login,
            test_google_auth_endpoint,
            test_forgot_password,
            test_reset_password_invalid_token
        ]
        
        passed = 0
        for test in tests:
            if test():
                passed += 1
        
        print("\n" + "=" * 50)
        print(f"🎯 Test Results: {passed}/{len(tests)} tests passed")
        
        if passed == len(tests):
            print("🎉 All tests passed! Authentication system is working correctly.")
        else:
            print("⚠️  Some tests failed. Check the output above for details.")
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure it's running on http://localhost:8000")

if __name__ == "__main__":
    main()
