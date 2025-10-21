"""
Authentication dependencies for FastAPI endpoints.
"""

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional
from database import get_db
from models.user import User, UserRole
from models.tenant import Tenant
from services.auth_service import auth_service

# Security scheme for bearer token
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency to get the current authenticated user from JWT token.

    Args:
        credentials: HTTP Authorization header with bearer token
        db: Database session

    Returns:
        User: Current authenticated user

    Raises:
        HTTPException: 401 if token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Decode token
    token = credentials.credentials
    payload = auth_service.decode_access_token(token)

    if payload is None:
        raise credentials_exception

    # Extract user_id from token
    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    # Get user from database
    user = db.query(User).filter(User.user_id == user_id).first()

    if user is None:
        raise credentials_exception

    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to get current active user.

    Args:
        current_user: User from get_current_user dependency

    Returns:
        User: Active user

    Raises:
        HTTPException: 403 if user is not active
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user


def require_role(*allowed_roles: UserRole):
    """
    Dependency factory to require specific roles.

    Usage:
        @app.get("/admin-only")
        def admin_endpoint(user: User = Depends(require_role(UserRole.ADMIN))):
            ...

        @app.get("/admin-or-analyst")
        def endpoint(user: User = Depends(require_role(UserRole.ADMIN, UserRole.ANALYST))):
            ...

    Args:
        *allowed_roles: One or more UserRole values that are allowed

    Returns:
        Dependency function that checks user role
    """
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role: {', '.join([r.value for r in allowed_roles])}"
            )
        return current_user

    return role_checker


# Convenience dependencies for common roles
RequireAdmin = require_role(UserRole.ADMIN)
RequireAnalyst = require_role(UserRole.ADMIN, UserRole.ANALYST)
RequireAny = require_role(UserRole.ADMIN, UserRole.ANALYST, UserRole.VIEWER)


async def get_optional_user(
    request: Request,
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Dependency to get current user if token is provided, None otherwise.
    Useful for endpoints that work both authenticated and unauthenticated.

    Args:
        request: FastAPI request object
        db: Database session

    Returns:
        User or None: Current user if authenticated, None otherwise
    """
    auth_header = request.headers.get("authorization")

    if not auth_header or not auth_header.startswith("Bearer "):
        return None

    token = auth_header.split(" ")[1]
    payload = auth_service.decode_access_token(token)

    if payload is None:
        return None

    user_id = payload.get("sub")
    if user_id is None:
        return None

    user = db.query(User).filter(User.user_id == user_id).first()
    return user


def verify_tenant_access(current_user: User, tenant_id: str) -> bool:
    """
    Verify that the current user has access to the specified tenant.

    Args:
        current_user: Current authenticated user
        tenant_id: Tenant ID to check access for

    Returns:
        bool: True if user has access, False otherwise
    """
    return str(current_user.tenant_id) == tenant_id


async def get_current_user_with_tenant_check(
    tenant_id: str,
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to verify user belongs to the specified tenant.

    Args:
        tenant_id: Tenant ID from path parameter
        current_user: Current authenticated user

    Returns:
        User: Current user if tenant matches

    Raises:
        HTTPException: 403 if user doesn't belong to tenant
    """
    if not verify_tenant_access(current_user, tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this tenant's resources"
        )
    return current_user
