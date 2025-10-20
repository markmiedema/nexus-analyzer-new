"""
State Tax Configuration model for state-specific tax information.
"""

from sqlalchemy import Column, String, DateTime, Numeric, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from database import Base


class StateTaxConfig(Base):
    """
    State tax configuration containing tax rates and state-specific information.
    Reference data for all 50 states + DC.
    """
    __tablename__ = "state_tax_config"

    config_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False
    )

    # State identification
    state_code = Column(String(2), unique=True, nullable=False, index=True)
    state_name = Column(String(50), nullable=False)

    # Tax rates
    state_tax_rate = Column(Numeric(5, 4), nullable=False)  # e.g., 0.0650 for 6.5%
    avg_local_tax_rate = Column(Numeric(5, 4), default=0, nullable=False)
    min_combined_rate = Column(Numeric(5, 4), nullable=True)
    max_combined_rate = Column(Numeric(5, 4), nullable=True)

    # Sales tax status
    has_sales_tax = Column(Boolean, default=True, nullable=False)
    sales_tax_name = Column(String(100), nullable=True)  # e.g., "Sales and Use Tax"

    # Origin vs Destination sourcing
    is_destination_based = Column(Boolean, default=True, nullable=False)
    is_origin_based = Column(Boolean, default=False, nullable=False)

    # Local taxes
    has_local_taxes = Column(Boolean, default=False, nullable=False)
    local_tax_administered_by_state = Column(Boolean, default=True, nullable=False)

    # Filing information
    filing_frequency_options = Column(Text, nullable=True)  # Monthly, Quarterly, Annual
    filing_threshold_for_frequency = Column(Text, nullable=True)

    # Economic nexus lookback
    default_lookback_months = Column(String(10), default="36", nullable=False)  # Default 3 years

    # Penalty and interest rates
    late_filing_penalty_rate = Column(Numeric(5, 2), nullable=True)
    late_payment_penalty_rate = Column(Numeric(5, 2), nullable=True)
    interest_rate_annual = Column(Numeric(5, 4), nullable=True)

    # Exemptions
    common_exemptions = Column(Text, nullable=True)  # Common exempt categories

    # Registration
    registration_url = Column(String(500), nullable=True)
    tax_agency_name = Column(String(255), nullable=True)
    tax_agency_website = Column(String(500), nullable=True)

    # Additional notes
    special_notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<StateTaxConfig {self.state_code} - {self.state_name}>"
