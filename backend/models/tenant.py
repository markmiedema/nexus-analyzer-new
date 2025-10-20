"""
Tenant (Organization) model for multi-tenancy support.
"""

from sqlalchemy import Column, String, DateTime, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from database import Base


class TenantStatus(str, enum.Enum):
    """Tenant account status."""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TRIAL = "trial"
    CANCELLED = "cancelled"


class SubscriptionPlan(str, enum.Enum):
    """Subscription plan types."""
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class Tenant(Base):
    """
    Tenant/Organization model for multi-tenant SaaS.
    Each tenant represents a separate organization using the platform.
    """
    __tablename__ = "tenants"

    tenant_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False
    )
    company_name = Column(String(255), nullable=False)
    subdomain = Column(String(63), unique=True, nullable=False, index=True)

    # Branding
    logo_url = Column(String(500), nullable=True)
    primary_color = Column(String(7), default="#4F46E5")  # Indigo-600
    secondary_color = Column(String(7), default="#06B6D4")  # Cyan-500

    # Subscription
    subscription_plan = Column(
        SQLEnum(SubscriptionPlan),
        default=SubscriptionPlan.FREE,
        nullable=False
    )
    status = Column(
        SQLEnum(TenantStatus),
        default=TenantStatus.TRIAL,
        nullable=False,
        index=True
    )

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")
    analyses = relationship("Analysis", back_populates="tenant", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Tenant {self.company_name} ({self.subdomain})>"
