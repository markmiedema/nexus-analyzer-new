"""
Tenant management API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List
import uuid

from database import get_db
from models.tenant import Tenant, TenantStatus, SubscriptionPlan
from models.user import User, UserRole
from models.audit_log import AuditLog
from dependencies.auth import get_current_user, require_role
from pydantic import BaseModel, Field

router = APIRouter()


class TenantCreate(BaseModel):
    """Schema for creating a tenant."""
    company_name: str = Field(..., min_length=1, max_length=255)
    subdomain: str = Field(..., min_length=1, max_length=63)
    subscription_plan: SubscriptionPlan = SubscriptionPlan.FREE
    logo_url: str | None = None
    primary_color: str = "#4F46E5"
    secondary_color: str = "#06B6D4"


class TenantResponse(BaseModel):
    """Schema for tenant response."""
    tenant_id: str
    company_name: str
    subdomain: str
    logo_url: str | None
    primary_color: str
    secondary_color: str
    subscription_plan: SubscriptionPlan
    status: TenantStatus

    class Config:
        from_attributes = True


@router.post("", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    tenant_data: TenantCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Create a new tenant (system admin only).

    This endpoint should be restricted to system administrators.
    For MVP, it's available without authentication to allow initial setup.
    """

    # Check if subdomain already exists
    existing_tenant = db.query(Tenant).filter(
        Tenant.subdomain == tenant_data.subdomain
    ).first()

    if existing_tenant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Subdomain already exists"
        )

    # Create new tenant
    new_tenant = Tenant(
        tenant_id=uuid.uuid4(),
        company_name=tenant_data.company_name,
        subdomain=tenant_data.subdomain,
        subscription_plan=tenant_data.subscription_plan,
        status=TenantStatus.TRIAL,
        logo_url=tenant_data.logo_url,
        primary_color=tenant_data.primary_color,
        secondary_color=tenant_data.secondary_color
    )

    db.add(new_tenant)
    db.commit()
    db.refresh(new_tenant)

    # Log tenant creation
    audit_log = AuditLog(
        tenant_id=new_tenant.tenant_id,
        action="tenant_created",
        resource_type="tenant",
        resource_id=new_tenant.tenant_id,
        ip_address=request.client.host if request.client else None,
        success=True,
        description=f"Tenant {new_tenant.company_name} created"
    )
    db.add(audit_log)
    db.commit()

    return new_tenant


@router.get("/me", response_model=TenantResponse)
async def get_current_tenant_info(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current tenant information."""

    tenant = db.query(Tenant).filter(
        Tenant.tenant_id == current_user.tenant_id
    ).first()

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )

    return tenant


@router.get("/{tenant_id}", response_model=TenantResponse)
async def get_tenant(
    tenant_id: str,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """Get tenant by ID (admin only)."""

    # Verify user has access to this tenant
    if str(current_user.tenant_id) != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    tenant = db.query(Tenant).filter(Tenant.tenant_id == tenant_id).first()

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )

    return tenant
