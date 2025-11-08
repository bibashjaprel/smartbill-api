from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import datetime
import uuid


# =========================================================
# 🧩 Base User Schemas
# =========================================================

class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    is_active: Optional[bool] = True


class UserCreate(UserBase):
    password: str


class UserSignup(BaseModel):
    """Enhanced signup schema with password confirmation"""
    full_name: str
    email: EmailStr
    password: str
    confirm_password: str
    
    @validator('confirm_password')
    def passwords_match(cls, v, values, **kwargs):
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v
    
    @validator('full_name')
    def validate_full_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Full name is required')
        if len(v.strip()) < 2:
            raise ValueError('Full name must be at least 2 characters long')
        return v.strip()
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters long')
        return v


class UserUpdate(UserBase):
    password: Optional[str] = None


class UserInDBBase(UserBase):
    id: uuid.UUID
    is_verified: bool
    role: str
    shop_id: Optional[uuid.UUID] = None
    google_id: Optional[str] = None
    profile_picture: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True  # For ORM mode


class User(UserInDBBase):
    """Public-facing User schema (without password)"""
    pass


class UserInDB(UserInDBBase):
    """Internal schema including hashed password"""
    password: Optional[str] = None


# =========================================================
# 🏪 Multi-Shop Role & Profile Management
# =========================================================

class UserShop(BaseModel):
    shop_id: uuid.UUID
    shop_name: str
    role: str  # super_admin, platform_admin, shop_owner, admin, manager, employee
    is_current: bool
    joined_at: datetime

    class Config:
        from_attributes = True


class UserProfile(UserInDBBase):
    current_shop_id: Optional[uuid.UUID] = None
    shops: List[UserShop] = Field(default_factory=list)

    class Config:
        from_attributes = True


class SetCurrentShopRequest(BaseModel):
    shop_id: uuid.UUID


# =========================================================
# 🔐 Role Hierarchy for Multi-Tenant Platform
# =========================================================

class UserRole:
    """User role constants and hierarchy management for multi-tenant platform"""

    # Platform-level roles (manage the entire system)
    SUPER_ADMIN = "super_admin"
    PLATFORM_ADMIN = "platform_admin"

    # Shop-level roles (limited to specific shops)
    SHOP_OWNER = "shop_owner"
    ADMIN = "admin"
    MANAGER = "manager"
    EMPLOYEE = "employee"

    # Legacy alias
    OWNER = SHOP_OWNER

    # Hierarchy definition
    _hierarchy = {
        SUPER_ADMIN: 1,
        PLATFORM_ADMIN: 2,
        SHOP_OWNER: 3,
        ADMIN: 4,
        MANAGER: 5,
        EMPLOYEE: 6
    }

    @classmethod
    def get_hierarchy_level(cls, role: str) -> int:
        """Return hierarchy level (lower number = higher permission)"""
        return cls._hierarchy.get(role, 99)

    @classmethod
    def can_access(cls, user_role: str, required_role: str) -> bool:
        """Check if user role has sufficient permissions"""
        return cls.get_hierarchy_level(user_role) <= cls.get_hierarchy_level(required_role)

    @classmethod
    def is_platform_role(cls, role: str) -> bool:
        """Check if role is platform-level (can manage multiple shops)"""
        return role in [cls.SUPER_ADMIN, cls.PLATFORM_ADMIN]

    @classmethod
    def is_shop_role(cls, role: str) -> bool:
        """Check if role is shop-level (limited to one shop)"""
        return role in [cls.SHOP_OWNER, cls.ADMIN, cls.MANAGER, cls.EMPLOYEE]

    @classmethod
    def all_roles(cls) -> List[str]:
        """Return list of all valid roles"""
        return list(cls._hierarchy.keys())


# =========================================================
# 🧭 Validation Models for Requests
# =========================================================

class GoogleUserInfo(BaseModel):
    id: str
    email: EmailStr
    name: str
    picture: Optional[str] = None


class GoogleAuthRequest(BaseModel):
    token: str


class EmailVerificationRequest(BaseModel):
    email: EmailStr


class EmailVerificationConfirm(BaseModel):
    token: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class AdminResetPasswordRequest(BaseModel):
    vendor_email: EmailStr
    new_password: str


# =========================================================
# 🧩 Extra: Role Validation Hook
# =========================================================

# Add role validation to user models
for cls in [UserInDBBase, UserShop]:
    @validator("role", pre=True, allow_reuse=True)
    def validate_role(cls, value):
        """Ensure role is one of the predefined roles"""
        if value not in UserRole.all_roles():
            raise ValueError(f"Invalid role: {value}")
        return value
