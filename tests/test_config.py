"""
Configuration and common utilities for test scripts
"""
import os
import json
import requests
from typing import Dict, Any

# API Configuration
BASE_URL = "http://localhost:8000"
API_V1_PREFIX = "/api/v1"

# Test User Data
TEST_USER = {
    "email": "test@example.com",
    "password": "testpassword123",
    "confirm_password": "testpassword123",
    "full_name": "Test User"
}

# OAuth2 Form Data (for login)
LOGIN_FORM_DATA = {
    "grant_type": "",  # OAuth2 password flow
    "username": "test@example.com",  # Email is used as username
    "password": "testpassword123",
    "scope": "",
    "client_id": "",
    "client_secret": ""
}

# Test Product Data
TEST_PRODUCT = {
    "name": "Test Product",
    "description": "A test product for API testing",
    "price": 999.99,
    "quantity": 100,
    "category": "Test Category"
}

class APIClient:
    def __init__(self):
        self.base_url = BASE_URL
        self.api_prefix = API_V1_PREFIX
        self.token = None
        self.headers = {"Content-Type": "application/json"}
    
    def _url(self, endpoint: str) -> str:
        """Construct full URL for the endpoint"""
        return f"{self.base_url}{self.api_prefix}{endpoint}"
    
    def set_token(self, token: str):
        """Set authentication token for subsequent requests"""
        self.token = token
        self.headers["Authorization"] = f"Bearer {token}"
    
    def post(self, endpoint: str, data: Dict[str, Any], headers: Dict[str, str] = None) -> requests.Response:
        """Make POST request to the API"""
        url = self._url(endpoint)
        request_headers = headers if headers is not None else self.headers
        if headers and headers.get("Content-Type") == "application/x-www-form-urlencoded":
            return requests.post(url, data=data, headers=request_headers)
        return requests.post(url, json=data, headers=request_headers)
    
    def get(self, endpoint: str) -> requests.Response:
        """Make GET request to the API"""
        url = self._url(endpoint)
        return requests.get(url, headers=self.headers)
    
    def put(self, endpoint: str, data: Dict[str, Any]) -> requests.Response:
        """Make PUT request to the API"""
        url = self._url(endpoint)
        return requests.put(url, json=data, headers=self.headers)
    
    def delete(self, endpoint: str) -> requests.Response:
        """Make DELETE request to the API"""
        url = self._url(endpoint)
        return requests.delete(url, headers=self.headers)

def print_response(response: requests.Response):
    """Pretty print API response"""
    print(f"\nStatus Code: {response.status_code}")
    try:
        print("Response:")
        print(json.dumps(response.json(), indent=2))
    except:
        print("Response:", response.text)