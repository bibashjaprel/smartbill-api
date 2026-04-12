from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ...core.database import get_db
from ...crud.user import user as crud_user
from ...schemas.user import AdminResetPasswordRequest, User
from ...api.deps import get_current_admin_user
from ...models.shop import Shop as ShopModel

router = APIRouter()


class ShopSubscriptionUpdate(BaseModel):
    plan: str | None = None
    subscription_plan: str | None = None


class ShopStatusUpdate(BaseModel):
    status: str | None = None
    is_active: bool | None = None


_shop_plan_cache: dict[str, str] = {}


def _serialize_shop(shop: ShopModel):
    plan = _shop_plan_cache.get(str(shop.id), "trial")
    status_value = "active"
    owner_email = "unknown@shop.local"

    if getattr(shop, "owner", None):
        owner_email = shop.owner.email or owner_email
        if shop.owner.is_active is False:
            status_value = "paused"

    return {
        "id": str(shop.id),
        "name": shop.name,
        "owner_email": owner_email,
        "subscription_plan": plan,
        "status": status_value,
        "monthly_revenue": 0,
        "next_billing_date": "-",
    }


@router.post("/vendors/reset-password")
def admin_reset_vendor_password(
    reset_request: AdminResetPasswordRequest,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)
):
    """
    Admin endpoint to reset vendor password directly
    Only admins can access this endpoint
    """
    vendor = crud_user.get_by_email(db, email=reset_request.vendor_email)
    if not vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor not found"
        )
    
    # Check if the target user is an admin (admins can't reset other admin passwords this way)
    if crud_user.is_admin(vendor):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot reset password for admin users. Use proper admin tools."
        )
    
    if vendor.google_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This vendor uses Google Sign-In. Password reset is not applicable."
        )
    
    # Validate password strength
    if len(reset_request.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long"
        )
    
    vendor = crud_user.reset_password(db, user=vendor, new_password=reset_request.new_password)
    
    return {
        "message": f"Password reset successfully for vendor {vendor.email}",
        "vendor_email": vendor.email,
        "reset_by_admin": current_admin.email
    }


@router.get("/vendors")
def list_vendors(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
    skip: int = 0,
    limit: int = 100
):
    """
    Admin endpoint to list all vendors (non-admin users)
    """
    admin_roles = ["super_admin", "platform_admin", "admin"]
    vendors = db.query(crud_user.model).filter(
        ~crud_user.model.role.in_(admin_roles)
    ).offset(skip).limit(limit).all()
    
    return {
        "vendors": [User.from_orm(vendor) for vendor in vendors],
        "total": len(vendors)
    }


@router.get("/vendors/{vendor_id}")
def get_vendor(
    vendor_id: str,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)
):
    """
    Admin endpoint to get specific vendor details
    """
    vendor = crud_user.get(db, id=vendor_id)
    if not vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor not found"
        )
    
    if crud_user.is_admin(vendor):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This endpoint is for vendors only"
        )
    
    return User.from_orm(vendor)


@router.get("/shops")
def list_platform_shops(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
    skip: int = 0,
    limit: int = 200,
):
    shops = db.query(ShopModel).offset(skip).limit(limit).all()
    return [_serialize_shop(shop) for shop in shops]


@router.patch("/shops/{shop_id}/subscription")
def update_shop_subscription(
    shop_id: str,
    payload: ShopSubscriptionUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
):
    shop = db.query(ShopModel).filter(ShopModel.id == shop_id).first()
    if not shop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shop not found")

    selected_plan = (payload.plan or payload.subscription_plan or "trial").strip().lower()
    if selected_plan not in {"trial", "basic", "pro", "enterprise"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid plan")

    _shop_plan_cache[str(shop.id)] = selected_plan
    response = _serialize_shop(shop)
    response["subscription_plan"] = selected_plan
    return response


@router.patch("/shops/{shop_id}/status")
def update_shop_status(
    shop_id: str,
    payload: ShopStatusUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
):
    shop = db.query(ShopModel).filter(ShopModel.id == shop_id).first()
    if not shop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shop not found")

    if payload.is_active is not None:
        desired_active = payload.is_active
    else:
        desired_status = (payload.status or "active").strip().lower()
        if desired_status not in {"active", "paused", "cancelled"}:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid status")
        desired_active = desired_status == "active"

    if getattr(shop, "owner", None):
        shop.owner.is_active = desired_active
        db.add(shop.owner)
        db.commit()
        db.refresh(shop)

    return _serialize_shop(shop)
