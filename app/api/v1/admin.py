from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ...core.database import get_db
from ...crud.user import user as crud_user
from ...schemas.user import AdminResetPasswordRequest, User
from ...api.deps import get_current_admin_user

router = APIRouter()


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
    vendors = db.query(crud_user.model).filter(
        crud_user.model.is_admin == False
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
