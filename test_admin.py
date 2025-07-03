"""
Test cases for admin functionality
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.core.database import get_db
from app.crud.user import user as crud_user
from app.schemas.user import UserCreate
from app.core.security import get_password_hash

client = TestClient(app)

# Test data
ADMIN_USER = {
    "email": "admin@billsmart.com",
    "password": "adminpassword123",
    "full_name": "Admin User"
}

VENDOR_USER = {
    "email": "vendor@billsmart.com", 
    "password": "vendorpassword123",
    "full_name": "Vendor User"
}

def setup_test_users(db: Session):
    """Create test admin and vendor users"""
    # Create admin user
    admin_user = crud_user.create(db, obj_in=UserCreate(**ADMIN_USER))
    admin_user.is_verified = True
    admin_user.is_admin = True
    db.add(admin_user)
    
    # Create vendor user  
    vendor_user = crud_user.create(db, obj_in=UserCreate(**VENDOR_USER))
    vendor_user.is_verified = True
    vendor_user.is_admin = False
    db.add(vendor_user)
    
    db.commit()
    return admin_user, vendor_user

def get_auth_token(email: str, password: str) -> str:
    """Get authentication token for user"""
    response = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password}
    )
    assert response.status_code == 200
    return response.json()["access_token"]

def test_admin_reset_vendor_password():
    """Test admin can reset vendor password"""
    db = next(get_db())
    
    # Setup test users
    admin_user, vendor_user = setup_test_users(db)
    
    # Get admin token
    admin_token = get_auth_token(ADMIN_USER["email"], ADMIN_USER["password"])
    
    # Admin resets vendor password
    new_password = "newvendorpassword123"
    response = client.post(
        "/api/v1/admin/vendors/reset-password",
        json={
            "vendor_email": VENDOR_USER["email"],
            "new_password": new_password
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["vendor_email"] == VENDOR_USER["email"]
    assert data["reset_by_admin"] == ADMIN_USER["email"]
    
    # Test vendor can login with new password
    response = client.post(
        "/api/v1/auth/login",
        data={"username": VENDOR_USER["email"], "password": new_password}
    )
    assert response.status_code == 200

def test_vendor_cannot_access_admin_endpoints():
    """Test vendor cannot access admin endpoints"""
    db = next(get_db())
    
    # Setup test users
    admin_user, vendor_user = setup_test_users(db)
    
    # Get vendor token
    vendor_token = get_auth_token(VENDOR_USER["email"], VENDOR_USER["password"])
    
    # Try to access admin endpoint
    response = client.post(
        "/api/v1/admin/vendors/reset-password",
        json={
            "vendor_email": "someone@example.com",
            "new_password": "newpassword123"
        },
        headers={"Authorization": f"Bearer {vendor_token}"}
    )
    
    assert response.status_code == 403
    assert "Not enough permissions" in response.json()["detail"]

def test_admin_cannot_reset_admin_password():
    """Test admin cannot reset another admin's password via vendor endpoint"""
    db = next(get_db())
    
    # Setup test users
    admin_user, vendor_user = setup_test_users(db)
    
    # Create another admin
    admin2_data = {
        "email": "admin2@billsmart.com",
        "password": "admin2password123", 
        "full_name": "Admin 2"
    }
    admin2 = crud_user.create(db, obj_in=UserCreate(**admin2_data))
    admin2.is_verified = True
    admin2.is_admin = True
    db.add(admin2)
    db.commit()
    
    # Get first admin token
    admin_token = get_auth_token(ADMIN_USER["email"], ADMIN_USER["password"])
    
    # Try to reset another admin's password
    response = client.post(
        "/api/v1/admin/vendors/reset-password",
        json={
            "vendor_email": admin2_data["email"],
            "new_password": "newpassword123"
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 400
    assert "Cannot reset password for admin users" in response.json()["detail"]

def test_admin_list_vendors():
    """Test admin can list vendors"""
    db = next(get_db())
    
    # Setup test users
    admin_user, vendor_user = setup_test_users(db)
    
    # Get admin token
    admin_token = get_auth_token(ADMIN_USER["email"], ADMIN_USER["password"])
    
    # List vendors
    response = client.get(
        "/api/v1/admin/vendors",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "vendors" in data
    assert len(data["vendors"]) >= 1
    
    # Check that vendor is in the list but admin is not
    vendor_emails = [v["email"] for v in data["vendors"]]
    assert VENDOR_USER["email"] in vendor_emails
    assert ADMIN_USER["email"] not in vendor_emails

def test_vendor_forgot_password_still_works():
    """Test that vendor forgot password flow still works"""
    db = next(get_db())
    
    # Setup test users
    admin_user, vendor_user = setup_test_users(db)
    
    # Vendor requests password reset
    response = client.post(
        "/api/v1/auth/forgot-password",
        json={"email": VENDOR_USER["email"]}
    )
    
    assert response.status_code == 200
    assert "password reset email has been sent" in response.json()["message"]

def test_admin_get_vendor_details():
    """Test admin can get specific vendor details"""
    db = next(get_db())
    
    # Setup test users
    admin_user, vendor_user = setup_test_users(db)
    
    # Get admin token
    admin_token = get_auth_token(ADMIN_USER["email"], ADMIN_USER["password"])
    
    # Get vendor details
    response = client.get(
        f"/api/v1/admin/vendors/{vendor_user.id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == VENDOR_USER["email"]
    assert data["is_admin"] == False

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
