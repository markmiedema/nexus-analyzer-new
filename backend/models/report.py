"""
Report model for generated PDF reports.
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from database import Base


class ReportType(str, enum.Enum):
    """Type of report."""
    EXECUTIVE_SUMMARY = "executive_summary"
    DETAILED_ANALYSIS = "detailed_analysis"
    STATE_BY_STATE = "state_by_state"
    CUSTOM = "custom"


class ReportStatus(str, enum.Enum):
    """Report generation status."""
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


class Report(Base):
    """
    Generated PDF reports for analyses.
    Multiple reports can be generated per analysis.
    """
    __tablename__ = "reports"

    report_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False
    )

    # Analysis relationship
    analysis_id = Column(
        UUID(as_uuid=True),
        ForeignKey("analyses.analysis_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Report metadata
    report_type = Column(
        SQLEnum(ReportType),
        default=ReportType.EXECUTIVE_SUMMARY,
        nullable=False
    )
    report_name = Column(String(255), nullable=False)

    # File information
    file_path = Column(String(500), nullable=True)  # S3 path
    file_size_bytes = Column(Integer, nullable=True)

    # Generation status
    status = Column(
        SQLEnum(ReportStatus),
        default=ReportStatus.PENDING,
        nullable=False
    )
    error_message = Column(String(1000), nullable=True)

    # Report version
    version = Column(Integer, default=1, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    generated_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    analysis = relationship("Analysis", back_populates="reports")

    def __repr__(self):
        return f"<Report {self.report_type} for Analysis {self.analysis_id}>"
