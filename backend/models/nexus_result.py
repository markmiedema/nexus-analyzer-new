"""
Nexus Result model for storing nexus determination results.
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Numeric, Boolean, Date, Enum as SQLEnum, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from database import Base


class NexusDetermination(str, enum.Enum):
    """Nexus determination result."""
    HAS_NEXUS = "has_nexus"
    NO_NEXUS = "no_nexus"
    CLOSE_TO_THRESHOLD = "close_to_threshold"  # Within 10% of threshold


class NexusStatus(str, enum.Enum):
    """Nexus status - distinguishes between physical and economic nexus."""
    NEXUS_PHYSICAL = "nexus_physical"
    NEXUS_ECONOMIC = "nexus_economic"
    CLOSE_TO_THRESHOLD = "close_to_threshold"
    NO_NEXUS = "no_nexus"


class ConfidenceLevel(str, enum.Enum):
    """Confidence in nexus determination."""
    HIGH = "high"  # Clear threshold met/not met
    MEDIUM = "medium"  # Edge case or unclear data
    LOW = "low"  # Missing data or complex scenario


class NexusResult(Base):
    """
    Nexus determination result for a specific state in an analysis.
    One record per state per analysis.
    """
    __tablename__ = "nexus_results"

    result_id = Column(
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

    # State
    state = Column(String(2), nullable=False, index=True)

    # Nexus determination
    has_physical_nexus = Column(Boolean, default=False, nullable=False)
    has_economic_nexus = Column(Boolean, default=False, nullable=False)
    nexus_status = Column(
        SQLEnum(NexusStatus),
        nullable=False,
        index=True
    )
    overall_determination = Column(
        SQLEnum(NexusDetermination),
        nullable=False,
        index=True
    )

    # Economic nexus metrics
    total_sales = Column(Numeric(12, 2), default=0, nullable=False)
    total_transactions = Column(Integer, default=0, nullable=False)
    marketplace_sales = Column(Numeric(12, 2), default=0, nullable=False)
    non_marketplace_sales = Column(Numeric(12, 2), default=0, nullable=False)

    # Threshold comparison
    sales_threshold = Column(Numeric(12, 2), nullable=True)
    transaction_threshold = Column(Integer, nullable=True)
    sales_threshold_percentage = Column(Numeric(5, 2), nullable=True)  # % of threshold met
    transaction_threshold_percentage = Column(Numeric(5, 2), nullable=True)

    # Nexus establishment
    nexus_established_date = Column(Date, nullable=True)  # When threshold was first crossed
    registration_deadline = Column(Date, nullable=True)  # When to register

    # Confidence and notes
    confidence_level = Column(
        SQLEnum(ConfidenceLevel),
        default=ConfidenceLevel.MEDIUM,
        nullable=False
    )
    determination_notes = Column(Text, nullable=True)
    warnings = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    analysis = relationship("Analysis", back_populates="nexus_results")

    def __repr__(self):
        return f"<NexusResult {self.state} - {self.overall_determination}>"
