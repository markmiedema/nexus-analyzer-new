"""
User model for authentication and user management.
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from database import Base


class UserRole(str, enum.Enum):
    """User role types for RBAC."""
    ADMIN = "admin"  # Full access to tenant
    ANALYST = "analyst"  # Can create and view analyses
    VIEWER = "viewer"  # Read-only access


class User(Base):
    """
    User model with multi-tenant support.
    Each user belongs to one tenant.
    """
    __tablename__ = "users"

    user_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False
    )

    # Tenant relationship
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.tenant_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Authentication
    email = Column(String(255), nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)

    # Profile
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)

    # Authorization
    role = Column(
        SQLEnum(UserRole),
        default=UserRole.VIEWER,
        nullable=False
    )

    # Status
    is_active = Column(String(10), default="true", nullable=False)
    email_verified = Column(String(10), default="false", nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_login = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    tenant = relationship("Tenant", back_populates="users")
    created_analyses = relationship("Analysis", back_populates="created_by_user")

    # Unique constraint: one email per tenant
    __table_args__ = (
        {"schema": None},
    )

    @property
    def full_name(self):
        """Return user's full name."""
        return f"{self.first_name} {self.last_name}"

    def __repr__(self):
        return f"<User {self.email} ({self.role})>"
