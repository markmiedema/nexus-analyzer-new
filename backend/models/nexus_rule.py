"""
Nexus Rules model for state tax nexus thresholds.
"""

from sqlalchemy import Column, String, DateTime, Numeric, Date, Enum as SQLEnum, Integer, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
import enum
from database import Base


class NexusType(str, enum.Enum):
    """Type of nexus."""
    PHYSICAL = "physical"
    ECONOMIC = "economic"
    AFFILIATE = "affiliate"
    CLICK_THROUGH = "click_through"


class ThresholdMeasurement(str, enum.Enum):
    """How the threshold is measured."""
    SALES_ONLY = "sales_only"  # Only revenue threshold
    TRANSACTIONS_ONLY = "transactions_only"  # Only transaction count
    SALES_OR_TRANSACTIONS = "sales_or_transactions"  # Either threshold
    SALES_AND_TRANSACTIONS = "sales_and_transactions"  # Both thresholds


class MeasurementPeriod(str, enum.Enum):
    """Time period for measuring thresholds."""
    CALENDAR_YEAR = "calendar_year"  # Current calendar year
    ROLLING_12_MONTHS = "rolling_12_months"  # Previous 12 months
    PREVIOUS_CALENDAR_YEAR = "previous_calendar_year"  # Last year


class NexusRule(Base):
    """
    Nexus rules and thresholds for each state.
    Defines when a business establishes nexus in a state.
    """
    __tablename__ = "nexus_rules"

    rule_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False
    )

    # State and nexus type
    state_code = Column(String(2), nullable=False, index=True)  # Two-letter state code
    state_name = Column(String(50), nullable=True)  # Full state name (optional)
    nexus_type = Column(
        SQLEnum(NexusType),
        nullable=False
    )

    # Economic nexus thresholds
    sales_threshold = Column(Numeric(12, 2), nullable=True)
    transaction_threshold = Column(Integer, nullable=True)

    # How thresholds are evaluated
    threshold_measurement = Column(
        SQLEnum(ThresholdMeasurement),
        nullable=True
    )
    measurement_period = Column(
        SQLEnum(MeasurementPeriod),
        nullable=True
    )

    # Marketplace facilitator rules
    marketplace_facilitator_law = Column(Boolean, default=False, nullable=False)
    marketplace_sales_excluded = Column(Boolean, default=True, nullable=False)

    # Effective dates
    effective_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)

    # Rule details
    rule_description = Column(String(1000), nullable=True)
    registration_url = Column(String(500), nullable=True)
    rule_source_url = Column(String(500), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    @property
    def state(self):
        """Backwards compatibility property - returns state_code."""
        return self.state_code

    def __repr__(self):
        return f"<NexusRule {self.state_code} {self.nexus_type}>"
