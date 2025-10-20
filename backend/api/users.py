"""
User management API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models.user import User, UserRole
from schemas.auth import UserResponse
from dependencies.auth import get_current_user, require_role

router = APIRouter()


@router.get("", response_model=List[UserResponse])
async def list_users(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """
    List all users in the current tenant.

    Only returns users belonging to the authenticated user's tenant.
    """

    users = db.query(User).filter(
        User.tenant_id == current_user.tenant_id
    ).offset(skip).limit(limit).all()

    return users


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user by ID."""

    user = db.query(User).filter(
        User.user_id == user_id,
        User.tenant_id == current_user.tenant_id  # Ensure same tenant
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return user


@router.patch("/{user_id}/role", response_model=UserResponse)
async def update_user_role(
    user_id: str,
    new_role: UserRole,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Update user role (admin only).

    Only admins can change user roles.
    """

    user = db.query(User).filter(
        User.user_id == user_id,
        User.tenant_id == current_user.tenant_id
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Prevent user from removing their own admin role
    if user.user_id == current_user.user_id and new_role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove your own admin role"
        )

    user.role = new_role
    db.commit()
    db.refresh(user)

    return user


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Delete user (admin only).

    Permanently removes a user from the system.
    """

    user = db.query(User).filter(
        User.user_id == user_id,
        User.tenant_id == current_user.tenant_id
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Prevent user from deleting themselves
    if user.user_id == current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )

    db.delete(user)
    db.commit()

    return {"message": "User deleted successfully"}
