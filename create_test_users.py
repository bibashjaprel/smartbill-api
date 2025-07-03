"""
Script to create test admin and vendor users for manual testing
"""
from app.crud.user import user as crud_user
from app.schemas.user import UserCreate
from app.core.database import get_db

def create_test_users():
    """Create admin and vendor test users"""
    db = next(get_db())
    
    # Admin user
    admin_data = UserCreate(
        email="admin@billsmart.com",
        password="adminpassword123",
        full_name="Admin User"
    )
    
    # Check if admin exists
    existing_admin = crud_user.get_by_email(db, email=admin_data.email)
    if not existing_admin:
        admin_user = crud_user.create(db, obj_in=admin_data)
        admin_user.is_verified = True
        admin_user.is_admin = True
        db.add(admin_user)
        db.commit()
        print(f"✅ Created admin user: {admin_user.email}")
    else:
        print(f"ℹ️  Admin user already exists: {existing_admin.email}")
        # Update to ensure it's admin
        existing_admin.is_admin = True
        existing_admin.is_verified = True
        db.add(existing_admin)
        db.commit()
        print(f"✅ Updated admin user: {existing_admin.email}")
    
    # Vendor user
    vendor_data = UserCreate(
        email="vendor@billsmart.com",
        password="vendorpassword123", 
        full_name="Vendor User"
    )
    
    # Check if vendor exists
    existing_vendor = crud_user.get_by_email(db, email=vendor_data.email)
    if not existing_vendor:
        vendor_user = crud_user.create(db, obj_in=vendor_data)
        vendor_user.is_verified = True
        vendor_user.is_admin = False
        db.add(vendor_user)
        db.commit()
        print(f"✅ Created vendor user: {vendor_user.email}")
    else:
        print(f"ℹ️  Vendor user already exists: {existing_vendor.email}")
        # Update to ensure it's not admin
        existing_vendor.is_admin = False
        existing_vendor.is_verified = True
        db.add(existing_vendor)
        db.commit()
        print(f"✅ Updated vendor user: {existing_vendor.email}")

if __name__ == "__main__":
    create_test_users()
