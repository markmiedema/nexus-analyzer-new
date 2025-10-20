"""
Liability Estimate model for tax liability calculations.
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Numeric, Integer, Text, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from database import Base


class RiskLevel(str, enum.Enum):
    """Risk level for non-compliance."""
    HIGH = "high"  # Large liability, clear nexus
    MEDIUM = "medium"  # Moderate liability
    LOW = "low"  # Small liability or unclear nexus


class LiabilityEstimate(Base):
    """
    Tax liability estimate for a specific state in an analysis.
    Calculates potential tax owed based on transaction data.
    """
    __tablename__ = "liability_estimates"

    estimate_id = Column(
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

    # Sales figures
    gross_sales = Column(Numeric(12, 2), default=0, nullable=False)
    marketplace_sales = Column(Numeric(12, 2), default=0, nullable=False)
    exempt_sales = Column(Numeric(12, 2), default=0, nullable=False)
    taxable_sales = Column(Numeric(12, 2), default=0, nullable=False)

    # Tax rates
    state_tax_rate = Column(Numeric(5, 4), nullable=False)  # e.g., 0.0650 for 6.5%
    avg_local_tax_rate = Column(Numeric(5, 4), default=0, nullable=False)
    combined_tax_rate = Column(Numeric(5, 4), nullable=False)

    # Liability calculations
    estimated_liability_low = Column(Numeric(12, 2), nullable=False)  # State rate only
    estimated_liability_high = Column(Numeric(12, 2), nullable=False)  # State + avg local
    estimated_liability_mid = Column(Numeric(12, 2), nullable=False)  # Average of low/high

    # Lookback period liability
    lookback_period_months = Column(Integer, nullable=True)
    lookback_liability = Column(Numeric(12, 2), nullable=True)

    # Penalties and interest
    estimated_penalty_percentage = Column(Numeric(5, 2), default=10, nullable=False)
    estimated_interest_rate = Column(Numeric(5, 4), default=0.05, nullable=False)  # Annual rate
    estimated_penalty_amount = Column(Numeric(12, 2), nullable=True)
    estimated_interest_amount = Column(Numeric(12, 2), nullable=True)
    total_estimated_liability = Column(Numeric(12, 2), nullable=True)

    # Assumptions
    exemption_rate_assumed = Column(Numeric(5, 2), default=10, nullable=False)  # % of sales assumed exempt
    assumptions_notes = Column(Text, nullable=True)

    # Risk assessment
    risk_level = Column(
        SQLEnum(RiskLevel),
        default=RiskLevel.MEDIUM,
        nullable=False
    )
    risk_factors = Column(Text, nullable=True)

    # Recommendations
    recommended_action = Column(String(50), nullable=True)  # Register, Monitor, Review
    action_priority = Column(Integer, nullable=True)  # 1 = highest priority
    recommendation_notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    analysis = relationship("Analysis", back_populates="liability_estimates")

    def __repr__(self):
        return f"<LiabilityEstimate {self.state} ${self.estimated_liability_mid}>"
