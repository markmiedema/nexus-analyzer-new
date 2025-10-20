"""
Analysis model for nexus determination workflow.
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Enum as SQLEnum, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from database import Base


class AnalysisStatus(str, enum.Enum):
    """Analysis processing status."""
    PENDING = "pending"  # Created, not yet processing
    UPLOADING = "uploading"  # CSV upload in progress
    PROCESSING_CSV = "processing_csv"  # Parsing and validating CSV
    PROCESSING_NEXUS = "processing_nexus"  # Running nexus determination
    PROCESSING_LIABILITY = "processing_liability"  # Calculating liability
    GENERATING_REPORT = "generating_report"  # Creating PDF report
    COMPLETED = "completed"  # All processing complete
    FAILED = "failed"  # Processing failed
    CANCELLED = "cancelled"  # User cancelled


class Analysis(Base):
    """
    Analysis represents one nexus determination workflow.
    Contains metadata and orchestrates the entire analysis process.
    """
    __tablename__ = "analyses"

    analysis_id = Column(
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

    # Created by user
    created_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # Analysis metadata
    client_name = Column(String(255), nullable=False)
    analysis_date = Column(Date, server_default=func.current_date(), nullable=False)

    # Date range for analysis
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)

    # Processing status
    status = Column(
        SQLEnum(AnalysisStatus),
        default=AnalysisStatus.PENDING,
        nullable=False,
        index=True
    )
    error_message = Column(Text, nullable=True)

    # File references
    csv_file_path = Column(String(500), nullable=True)  # S3 path
    validation_report_path = Column(String(500), nullable=True)  # S3 path

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    tenant = relationship("Tenant", back_populates="analyses")
    created_by_user = relationship("User", back_populates="created_analyses")
    business_profile = relationship("BusinessProfile", back_populates="analysis", uselist=False, cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="analysis", cascade="all, delete-orphan")
    nexus_results = relationship("NexusResult", back_populates="analysis", cascade="all, delete-orphan")
    liability_estimates = relationship("LiabilityEstimate", back_populates="analysis", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="analysis", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Analysis {self.client_name} ({self.status})>"
