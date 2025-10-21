"""
Authentication API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from sqlalchemy.orm import Session
from datetime import datetime
import uuid

from database import get_db
from models.user import User, UserRole
from models.tenant import Tenant
from models.audit_log import AuditLog
from schemas.auth import (
    UserRegister,
    UserLogin,
    Token,
    UserResponse,
    PasswordChange
)
from services.auth_service import auth_service
from dependencies.auth import get_current_user, get_current_active_user
from middleware.tenant import get_current_tenant
from config import settings
from utils.rate_limit import limiter
from utils.cookies import set_auth_cookies, clear_auth_cookies

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(settings.RATE_LIMIT_AUTH)
async def register(
    user_data: UserRegister,
    request: Request,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant)
):
    """
    Register a new user.

    - **email**: Valid email address
    - **password**: Strong password (min 8 chars, uppercase, lowercase, digit)
    - **first_name**: User's first name
    - **last_name**: User's last name
    - **tenant_subdomain**: Optional tenant subdomain (can also be from request)
    """

    # Get tenant from request or user_data
    if not tenant and user_data.tenant_subdomain:
        tenant = db.query(Tenant).filter(
            Tenant.subdomain == user_data.tenant_subdomain
        ).first()

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant identification required"
        )

    # Check if user already exists
    existing_user = db.query(User).filter(
        User.email == user_data.email,
        User.tenant_id == tenant.tenant_id
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create new user
    hashed_password = auth_service.hash_password(user_data.password)

    new_user = User(
        user_id=uuid.uuid4(),
        tenant_id=tenant.tenant_id,
        email=user_data.email,
        password_hash=hashed_password,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        role=UserRole.VIEWER,  # Default role
        is_active=True,
        email_verified=False
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Log registration
    audit_log = AuditLog(
        tenant_id=tenant.tenant_id,
        user_id=new_user.user_id,
        action="user_registered",
        resource_type="user",
        resource_id=new_user.user_id,
        ip_address=request.client.host if request.client else None,
        success=True,
        description=f"User {new_user.email} registered"
    )
    db.add(audit_log)
    db.commit()

    # Convert UUIDs to strings for JSON serialization
    return UserResponse(
        user_id=str(new_user.user_id),
        tenant_id=str(new_user.tenant_id),
        email=new_user.email,
        first_name=new_user.first_name,
        last_name=new_user.last_name,
        role=new_user.role,
        is_active=new_user.is_active,
        email_verified=new_user.email_verified,
        created_at=new_user.created_at,
        last_login=new_user.last_login
    )


@router.post("/login", response_model=UserResponse)
@limiter.limit(settings.RATE_LIMIT_AUTH)
async def login(
    credentials: UserLogin,
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    Login and receive httpOnly cookies with access and refresh tokens.

    - **email**: User's email address
    - **password**: User's password
    - **tenant_subdomain**: Optional tenant subdomain

    Sets httpOnly cookies: access_token and refresh_token
    """

    # Get tenant
    tenant = None
    if credentials.tenant_subdomain:
        tenant = db.query(Tenant).filter(
            Tenant.subdomain == credentials.tenant_subdomain
        ).first()
    else:
        # Try to get from request state
        tenant = getattr(request.state, "tenant", None)

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant identification required"
        )

    # Find user
    user = db.query(User).filter(
        User.email == credentials.email,
        User.tenant_id == tenant.tenant_id
    ).first()

    if not user:
        # Log failed attempt
        audit_log = AuditLog(
            tenant_id=tenant.tenant_id,
            action="login_failed",
            resource_type="user",
            ip_address=request.client.host if request.client else None,
            success=False,
            description=f"Failed login attempt for {credentials.email}",
            error_message="Invalid credentials"
        )
        db.add(audit_log)
        db.commit()

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    # Verify password
    if not auth_service.verify_password(credentials.password, user.password_hash):
        # Log failed attempt
        audit_log = AuditLog(
            tenant_id=tenant.tenant_id,
            user_id=user.user_id,
            action="login_failed",
            resource_type="user",
            resource_id=user.user_id,
            ip_address=request.client.host if request.client else None,
            success=False,
            description=f"Failed login attempt for {credentials.email}",
            error_message="Invalid password"
        )
        db.add(audit_log)
        db.commit()

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()

    # Create access token
    token_data = auth_service.create_tokens_for_user(
        user_id=str(user.user_id),
        tenant_id=str(user.tenant_id),
        email=user.email,
        role=user.role.value
    )

    # Log successful login
    audit_log = AuditLog(
        tenant_id=tenant.tenant_id,
        user_id=user.user_id,
        action="login_success",
        resource_type="user",
        resource_id=user.user_id,
        ip_address=request.client.host if request.client else None,
        success=True,
        description=f"User {user.email} logged in"
    )
    db.add(audit_log)
    db.commit()

    # Set httpOnly cookies
    set_auth_cookies(response, token_data["access_token"], token_data["refresh_token"])

    # Return user data (tokens are in cookies now)
    return UserResponse(
        user_id=str(user.user_id),
        tenant_id=str(user.tenant_id),
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        role=user.role,
        is_active=user.is_active,
        email_verified=user.email_verified,
        created_at=user.created_at,
        last_login=user.last_login
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current user information.

    Requires authentication token in Authorization header.
    """
    # Convert UUIDs to strings for JSON serialization
    return UserResponse(
        user_id=str(current_user.user_id),
        tenant_id=str(current_user.tenant_id),
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        role=current_user.role,
        is_active=current_user.is_active,
        email_verified=current_user.email_verified,
        created_at=current_user.created_at,
        last_login=current_user.last_login
    )


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Logout user and clear httpOnly cookies.

    Clears access_token and refresh_token cookies.
    """

    # Log logout
    audit_log = AuditLog(
        tenant_id=current_user.tenant_id,
        user_id=current_user.user_id,
        action="logout",
        resource_type="user",
        resource_id=current_user.user_id,
        ip_address=request.client.host if request.client else None,
        success=True,
        description=f"User {current_user.email} logged out"
    )
    db.add(audit_log)
    db.commit()

    # Clear httpOnly cookies
    clear_auth_cookies(response)

    return {"message": "Successfully logged out"}


@router.post("/refresh", response_model=UserResponse)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def refresh_access_token(
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    Refresh access token using refresh token from httpOnly cookie.

    Returns new access and refresh tokens in httpOnly cookies.
    """
    # Get refresh token from cookie
    refresh_token = request.cookies.get("refresh_token")

    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No refresh token provided"
        )

    # Decode and validate refresh token
    payload = auth_service.decode_access_token(refresh_token)

    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    # Get user from database
    user_id = payload.get("sub")
    user = db.query(User).filter(User.user_id == user_id).first()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )

    # Create new tokens
    token_data = auth_service.create_tokens_for_user(
        user_id=str(user.user_id),
        tenant_id=str(user.tenant_id),
        email=user.email,
        role=user.role.value
    )

    # Set new cookies
    set_auth_cookies(response, token_data["access_token"], token_data["refresh_token"])

    # Log token refresh
    audit_log = AuditLog(
        tenant_id=user.tenant_id,
        user_id=user.user_id,
        action="token_refresh",
        resource_type="user",
        resource_id=user.user_id,
        ip_address=request.client.host if request.client else None,
        success=True,
        description=f"Access token refreshed for {user.email}"
    )
    db.add(audit_log)
    db.commit()

    # Return user data
    return UserResponse(
        user_id=str(user.user_id),
        tenant_id=str(user.tenant_id),
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        role=user.role,
        is_active=user.is_active,
        email_verified=user.email_verified,
        created_at=user.created_at,
        last_login=user.last_login
    )


@router.post("/change-password")
@limiter.limit(settings.RATE_LIMIT_AUTH)
async def change_password(
    request: Request,
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Change user password.

    Requires current password for verification.
    """

    # Verify current password
    if not auth_service.verify_password(
        password_data.current_password,
        current_user.password_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )

    # Hash new password
    new_password_hash = auth_service.hash_password(password_data.new_password)

    # Update password
    current_user.password_hash = new_password_hash
    db.commit()

    # Log password change
    audit_log = AuditLog(
        tenant_id=current_user.tenant_id,
        user_id=current_user.user_id,
        action="password_changed",
        resource_type="user",
        resource_id=current_user.user_id,
        success=True,
        description=f"User {current_user.email} changed password"
    )
    db.add(audit_log)
    db.commit()

    return {"message": "Password changed successfully"}
