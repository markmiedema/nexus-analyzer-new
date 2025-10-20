"""
Business Profile model for storing client business information.
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Boolean, Date
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from database import Base


class BusinessProfile(Base):
    """
    Business profile containing company information and business activities.
    One business profile per analysis.
    """
    __tablename__ = "business_profiles"

    profile_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False
    )

    # Analysis relationship (one-to-one)
    analysis_id = Column(
        UUID(as_uuid=True),
        ForeignKey("analyses.analysis_id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True
    )

    # Company information
    legal_business_name = Column(String(255), nullable=False)
    doing_business_as = Column(String(255), nullable=True)
    federal_ein = Column(String(20), nullable=True)

    # Business details
    business_structure = Column(String(50), nullable=True)  # LLC, Corp, Partnership, etc.
    industry = Column(String(100), nullable=True)
    naics_code = Column(String(10), nullable=True)

    # Business activities
    has_physical_presence = Column(Boolean, default=False, nullable=False)
    has_employees = Column(Boolean, default=False, nullable=False)
    has_inventory = Column(Boolean, default=False, nullable=False)
    uses_marketplace_facilitators = Column(Boolean, default=False, nullable=False)

    # Marketplace facilitators (e.g., Amazon, eBay)
    marketplace_facilitator_names = Column(ARRAY(String), nullable=True)

    # Product/Service types
    sells_tangible_goods = Column(Boolean, default=True, nullable=False)
    sells_digital_goods = Column(Boolean, default=False, nullable=False)
    sells_services = Column(Boolean, default=False, nullable=False)

    # Exemptions
    has_exempt_sales = Column(Boolean, default=False, nullable=False)
    exempt_customer_types = Column(ARRAY(String), nullable=True)  # Resale, Government, etc.

    # Additional notes
    notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    analysis = relationship("Analysis", back_populates="business_profile")
    physical_locations = relationship("PhysicalLocation", back_populates="business_profile", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<BusinessProfile {self.legal_business_name}>"
