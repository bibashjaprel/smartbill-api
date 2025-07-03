# Admin/Vendor Route Separation Implementation

## Overview

We have successfully implemented separate admin and vendor routes in the BillSmart API. This allows:

1. **Admins**: Can reset vendor passwords directly through admin endpoints
2. **Vendors**: Can only use the "forgot password" flow for self-service password reset

## Changes Made

### 1. Database Schema Updates

- Added `is_admin` boolean field to the `users` table
- Updated `database_schema.sql` with the new field
- Created migration script `add_admin_column_simple.py` to add the field to existing databases

### 2. Model Updates

**`app/models/user.py`**:
- Added `is_admin = Column(Boolean, default=False)` to User model

**`app/schemas/user.py`**:
- Added `is_admin: bool` field to user schemas
- Added `AdminResetPasswordRequest` schema for admin password resets
- Fixed deprecated `orm_mode` to `from_attributes`

### 3. CRUD Operations

**`app/crud/user.py`**:
- Added `is_admin(user: User) -> bool` method

### 4. Authentication & Authorization

**`app/api/deps.py`**:
- Added `get_current_admin_user()` dependency to check admin privileges
- This raises 403 Forbidden if the user is not an admin

### 5. New Admin Routes

**`app/api/v1/admin.py`** (New file):
```python
@router.post("/vendors/reset-password")  # Admin-only password reset
@router.get("/vendors")                  # List all vendors
@router.get("/vendors/{vendor_id}")      # Get specific vendor details
```

**Key Features**:
- All admin endpoints require admin authentication
- Admin cannot reset another admin's password via vendor endpoints
- Admin can reset any vendor's password directly
- Proper validation and error handling

### 6. Updated Auth Routes

**`app/api/v1/auth.py`**:
- Updated `/reset-password` endpoint documentation to clarify it's for self-service only
- Kept existing forgot password flow intact for vendors

### 7. Main Application

**`app/main.py`**:
- Added admin router with `/api/v1/admin` prefix

## API Endpoints

### Admin Endpoints (Require Admin Role)

#### Reset Vendor Password
```http
POST /api/v1/admin/vendors/reset-password
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "vendor_email": "vendor@example.com",
  "new_password": "newpassword123"
}
```

#### List Vendors
```http
GET /api/v1/admin/vendors?skip=0&limit=100
Authorization: Bearer <admin_token>
```

#### Get Vendor Details
```http
GET /api/v1/admin/vendors/{vendor_id}
Authorization: Bearer <admin_token>
```

### Vendor Endpoints (Self-Service)

#### Forgot Password (Email-based reset)
```http
POST /api/v1/auth/forgot-password
Content-Type: application/json

{
  "email": "vendor@example.com"
}
```

#### Reset Password (Token-based)
```http
POST /api/v1/auth/reset-password
Content-Type: application/json

{
  "token": "reset_token_from_email",
  "new_password": "newpassword123"
}
```

## Security Features

1. **Role-based Access Control**: Only admins can access admin endpoints
2. **Admin Protection**: Admins cannot reset other admin passwords via vendor endpoints
3. **Google OAuth Protection**: Cannot reset passwords for Google OAuth users
4. **Password Validation**: Minimum 8 characters for all password resets
5. **Audit Trail**: Admin password resets include admin email in response

## Error Handling

- **403 Forbidden**: Non-admin users accessing admin endpoints
- **404 Not Found**: Vendor not found
- **400 Bad Request**: 
  - Trying to reset admin password via vendor endpoint
  - Trying to reset Google OAuth user password
  - Invalid password (too short)
- **401 Unauthorized**: Invalid or missing authentication token

## Testing

Created comprehensive test suite in `test_admin.py`:
- Admin can reset vendor passwords
- Vendors cannot access admin endpoints
- Admin cannot reset other admin passwords via vendor endpoint
- Admin can list and view vendor details
- Vendor forgot password flow still works

## Migration Guide

### For Existing Databases

1. Run the migration script to add `is_admin` column:
```bash
python add_admin_column_simple.py
```

2. Create an admin user by setting `is_admin = true` in the database:
```sql
UPDATE users SET is_admin = true WHERE email = 'your_admin@example.com';
```

### For New Installations

The `is_admin` field is included in the database schema, so new installations will have it automatically.

## Usage Examples

### Create Admin User (Programmatically)
```python
from app.crud.user import user as crud_user
from app.schemas.user import UserCreate

# Create admin user
admin_data = UserCreate(
    email="admin@company.com",
    password="secure_password",
    full_name="Admin User"
)
admin_user = crud_user.create(db, obj_in=admin_data)
admin_user.is_admin = True
admin_user.is_verified = True
db.add(admin_user)
db.commit()
```

### Admin Workflow
1. Admin logs in to get access token
2. Admin can list all vendors
3. Admin can reset any vendor's password directly
4. Admin cannot reset other admin passwords

### Vendor Workflow
1. Vendor uses "forgot password" if they lose access
2. Vendor receives email with reset token
3. Vendor uses token to reset password
4. Vendor cannot access admin functions

## Benefits

1. **Clear Separation**: Distinct admin and vendor capabilities
2. **Security**: Proper role-based access control
3. **Audit Trail**: Track who performs administrative actions
4. **Self-Service**: Vendors can still reset their own passwords
5. **Scalability**: Easy to extend with more admin functions
6. **Backwards Compatibility**: Existing vendor functionality unchanged

## Future Enhancements

- Admin user management (create/disable admins)
- Admin audit logs
- Vendor approval workflows
- Role-based permissions (super admin, regular admin, etc.)
- Admin dashboard for vendor management
