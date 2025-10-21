"""
Audit Log model for tracking all system actions.
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Text, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from database import Base


class AuditLog(Base):
    """
    Audit log for tracking all important system actions.
    Records who did what and when for compliance and debugging.
    """
    __tablename__ = "audit_log"

    log_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False
    )

    # Tenant context
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.tenant_id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )

    # User who performed action
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # Action details
    action = Column(String(100), nullable=False, index=True)  # login, create_analysis, etc.
    resource_type = Column(String(50), nullable=True, index=True)  # analysis, user, tenant, etc.
    resource_id = Column(UUID(as_uuid=True), nullable=True, index=True)

    # Request details
    ip_address = Column(String(45), nullable=True)  # IPv6 max length
    user_agent = Column(String(500), nullable=True)

    # Additional context
    description = Column(Text, nullable=True)
    extra_data = Column('metadata', JSONB, nullable=True)  # Additional flexible data (column named 'metadata' in DB)

    # Result
    success = Column(Boolean, default=True, nullable=False, index=True)
    error_message = Column(Text, nullable=True)

    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    # Relationships
    tenant = relationship("Tenant")
    user = relationship("User")

    # Composite indexes for common queries
    __table_args__ = (
        Index('ix_audit_log_tenant_created', 'tenant_id', 'created_at'),
        Index('ix_audit_log_user_created', 'user_id', 'created_at'),
        Index('ix_audit_log_action_created', 'action', 'created_at'),
    )

    def __repr__(self):
        return f"<AuditLog {self.action} by {self.user_id}>"
