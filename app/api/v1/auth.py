from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from ...core.database import get_db
from ...core.config import settings
from ...core.security import create_access_token, create_email_verification_token, verify_email_verification_token, create_password_reset_token, verify_password_reset_token
from ...core.email import send_verification_email, send_password_reset_email
from ...core.google_auth import google_oauth
from ...crud.user import user as crud_user
from ...schemas.user import (
    User, UserCreate, LoginRequest, GoogleAuthRequest, 
    EmailVerificationRequest, EmailVerificationConfirm,
    ForgotPasswordRequest, ResetPasswordRequest
)
from ...api.deps import get_current_active_user

router = APIRouter()


@router.post("/login")
def login(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
):
    """
    Login for access token - now uses email in the username field
    """
    # OAuth2 form uses username field, but we treat it as email
    email = form_data.username
    password = form_data.password
    
    user = crud_user.authenticate(db, email=email, password=password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    elif not crud_user.is_active(user):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    elif not crud_user.is_verified(user):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email not verified. Please check your email for verification link."
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": User.from_orm(user)
    }


@router.post("/login-email")
def login_email(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Login with email and password (alternative endpoint)
    """
    user = crud_user.authenticate(db, email=login_data.email, password=login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    elif not crud_user.is_active(user):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    elif not crud_user.is_verified(user):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email not verified. Please check your email for verification link."
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": User.from_orm(user)
    }


@router.post("/google/login")
async def google_login(
    google_auth: GoogleAuthRequest,
    db: Session = Depends(get_db)
):
    """
    Google OAuth login
    """
    # Verify Google token
    user_info = await google_oauth.verify_token(google_auth.token)
    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Google token"
        )
    
    # Check if user exists by email
    user = crud_user.get_by_email(db, email=user_info["email"])
    
    if user:
        # User exists, update Google ID if not set
        if not user.google_id:
            user.google_id = user_info["id"]
            user.is_verified = True  # Mark as verified since Google verified the email
            if user_info.get("picture"):
                user.profile_picture = user_info["picture"]
            db.add(user)
            db.commit()
            db.refresh(user)
    else:
        # Create new user from Google info
        user = crud_user.create_google_user(
            db,
            email=user_info["email"],
            full_name=user_info["name"],
            google_id=user_info["id"],
            profile_picture=user_info.get("picture")
        )
    
    if not crud_user.is_active(user):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": User.from_orm(user)
    }


@router.post("/register", response_model=dict)
async def register(
    *,
    db: Session = Depends(get_db),
    user_in: UserCreate,
    background_tasks: BackgroundTasks
):
    """
    Create new user and send verification email
    """
    user = crud_user.get_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system."
        )
    
    user = crud_user.create(db, obj_in=user_in)
    
    # Generate verification token and send email
    verification_token = create_email_verification_token(user.email)
    background_tasks.add_task(
        send_verification_email,
        email=user.email,
        token=verification_token,
        user_name=user.full_name
    )
    
    return {
        "message": "User created successfully. Please check your email to verify your account.",
        "email": user.email
    }


@router.post("/verify-email")
def verify_email(
    verification_data: EmailVerificationConfirm,
    db: Session = Depends(get_db)
):
    """
    Verify email address
    """
    email = verify_email_verification_token(verification_data.token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )
    
    user = crud_user.get_by_email(db, email=email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already verified"
        )
    
    user = crud_user.verify_email(db, user=user)
    
    return {"message": "Email verified successfully"}


@router.post("/resend-verification")
async def resend_verification(
    verification_request: EmailVerificationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Resend email verification
    """
    user = crud_user.get_by_email(db, email=verification_request.email)
    if not user:
        # Don't reveal if email exists or not
        return {"message": "If the email exists, a verification email has been sent."}
    
    if user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already verified"
        )
    
    verification_token = create_email_verification_token(user.email)
    background_tasks.add_task(
        send_verification_email,
        email=user.email,
        token=verification_token,
        user_name=user.full_name
    )
    
    return {"message": "If the email exists, a verification email has been sent."}


@router.post("/forgot-password")
async def forgot_password(
    forgot_request: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Send password reset email
    """
    user = crud_user.get_by_email(db, email=forgot_request.email)
    if not user:
        # Don't reveal if email exists or not for security
        return {"message": "If the email exists, a password reset email has been sent."}
    
    # Only send reset email to verified users
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email not verified. Please verify your email first."
        )
    
    # Don't send reset email to OAuth users without passwords
    if not user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This account uses Google Sign-In. Please log in with Google."
        )
    
    reset_token = create_password_reset_token(user.email)
    background_tasks.add_task(
        send_password_reset_email,
        email=user.email,
        token=reset_token,
        user_name=user.full_name
    )
    
    return {"message": "If the email exists, a password reset email has been sent."}


@router.post("/reset-password")
def reset_password(
    reset_request: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Reset password with token (self-service forgot password flow)
    This endpoint is for users who forgot their password and received a reset token via email.
    For admin-initiated password resets, use the admin endpoints.
    """
    email = verify_password_reset_token(reset_request.token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired password reset token"
        )
    
    user = crud_user.get_by_email(db, email=email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if not user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This account uses Google Sign-In. Password reset is not applicable."
        )
    
    # Validate password strength
    if len(reset_request.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long"
        )
    
    user = crud_user.reset_password(db, user=user, new_password=reset_request.new_password)
    
    return {"message": "Password reset successfully"}


@router.post("/test-token", response_model=User)
def test_token(
    current_user: User = Depends(get_current_active_user)
):
    """
    Test access token
    """
    return current_user
