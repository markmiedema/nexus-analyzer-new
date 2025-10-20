"""
Physical Location model for tracking physical presence.
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Enum as SQLEnum, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from database import Base


class LocationType(str, enum.Enum):
    """Type of physical location."""
    OFFICE = "office"
    WAREHOUSE = "warehouse"
    RETAIL_STORE = "retail_store"
    MANUFACTURING = "manufacturing"
    REMOTE_EMPLOYEE = "remote_employee"
    OTHER = "other"


class PhysicalLocation(Base):
    """
    Physical location/presence in a state.
    Used to determine physical nexus.
    """
    __tablename__ = "physical_locations"

    location_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False
    )

    # Business profile relationship
    profile_id = Column(
        UUID(as_uuid=True),
        ForeignKey("business_profiles.profile_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Location type
    location_type = Column(
        SQLEnum(LocationType),
        nullable=False
    )

    # Address
    address_line1 = Column(String(255), nullable=False)
    address_line2 = Column(String(255), nullable=True)
    city = Column(String(100), nullable=False)
    state = Column(String(2), nullable=False, index=True)  # Two-letter state code
    zip_code = Column(String(10), nullable=False)

    # Additional info
    description = Column(String(500), nullable=True)

    # Dates
    established_date = Column(Date, nullable=True)
    closed_date = Column(Date, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    business_profile = relationship("BusinessProfile", back_populates="physical_locations")

    def __repr__(self):
        return f"<PhysicalLocation {self.location_type} in {self.state}>"
