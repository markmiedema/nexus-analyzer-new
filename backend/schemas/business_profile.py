"""
Pydantic schemas for business profile validation.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import date, datetime
from uuid import UUID
from models.physical_location import LocationType


# ==================== Physical Location Schemas ====================

class PhysicalLocationBase(BaseModel):
    """Base schema for physical location."""
    location_type: LocationType
    address_line1: str = Field(..., min_length=1, max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    city: str = Field(..., min_length=1, max_length=100)
    state: str = Field(..., min_length=2, max_length=2, pattern=r'^[A-Z]{2}$')
    zip_code: str = Field(..., pattern=r'^\d{5}(-\d{4})?$')
    description: Optional[str] = Field(None, max_length=500)
    established_date: Optional[date] = None
    closed_date: Optional[date] = None

    @validator('state')
    def validate_state(cls, v):
        """Validate state code."""
        from services.csv_processor import STATE_CODES
        if v.upper() not in STATE_CODES:
            raise ValueError(f"Invalid state code: {v}")
        return v.upper()

    @validator('closed_date')
    def validate_closed_date(cls, v, values):
        """Ensure closed date is after established date."""
        if v and 'established_date' in values and values['established_date']:
            if v < values['established_date']:
                raise ValueError("Closed date must be after established date")
        return v


class PhysicalLocationCreate(PhysicalLocationBase):
    """Schema for creating a physical location."""
    pass


class PhysicalLocationUpdate(BaseModel):
    """Schema for updating a physical location."""
    location_type: Optional[LocationType] = None
    address_line1: Optional[str] = Field(None, min_length=1, max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, min_length=1, max_length=100)
    state: Optional[str] = Field(None, min_length=2, max_length=2, pattern=r'^[A-Z]{2}$')
    zip_code: Optional[str] = Field(None, pattern=r'^\d{5}(-\d{4})?$')
    description: Optional[str] = Field(None, max_length=500)
    established_date: Optional[date] = None
    closed_date: Optional[date] = None

    @validator('state')
    def validate_state(cls, v):
        """Validate state code."""
        if v is None:
            return v
        from services.csv_processor import STATE_CODES
        if v.upper() not in STATE_CODES:
            raise ValueError(f"Invalid state code: {v}")
        return v.upper()


class PhysicalLocationResponse(PhysicalLocationBase):
    """Schema for physical location response."""
    location_id: UUID
    profile_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== Business Profile Schemas ====================

class BusinessProfileBase(BaseModel):
    """Base schema for business profile."""
    legal_business_name: str = Field(..., min_length=1, max_length=255)
    doing_business_as: Optional[str] = Field(None, max_length=255)
    federal_ein: Optional[str] = Field(None, pattern=r'^\d{2}-?\d{7}$')

    business_structure: Optional[str] = Field(None, max_length=50)
    industry: Optional[str] = Field(None, max_length=100)
    naics_code: Optional[str] = Field(None, pattern=r'^\d{2,6}$')

    has_physical_presence: bool = False
    has_employees: bool = False
    has_inventory: bool = False
    uses_marketplace_facilitators: bool = False

    marketplace_facilitator_names: Optional[List[str]] = None

    sells_tangible_goods: bool = True
    sells_digital_goods: bool = False
    sells_services: bool = False

    has_exempt_sales: bool = False
    exempt_customer_types: Optional[List[str]] = None

    notes: Optional[str] = None

    @validator('federal_ein')
    def validate_ein(cls, v):
        """Validate and format EIN."""
        if v is None:
            return v
        # Remove hyphens for validation
        ein = v.replace('-', '')
        if len(ein) != 9 or not ein.isdigit():
            raise ValueError("EIN must be 9 digits (format: XX-XXXXXXX)")
        # Return formatted
        return f"{ein[:2]}-{ein[2:]}"

    @validator('business_structure')
    def validate_business_structure(cls, v):
        """Validate business structure."""
        if v is None:
            return v
        valid_structures = [
            'Sole Proprietorship', 'Partnership', 'LLC', 'S-Corp',
            'C-Corp', 'Non-Profit', 'Other'
        ]
        if v not in valid_structures:
            raise ValueError(f"Business structure must be one of: {', '.join(valid_structures)}")
        return v

    @validator('marketplace_facilitator_names')
    def validate_marketplace_names(cls, v, values):
        """Ensure marketplace names provided if using facilitators."""
        if values.get('uses_marketplace_facilitators') and not v:
            raise ValueError("Marketplace facilitator names required when uses_marketplace_facilitators is True")
        return v

    @validator('exempt_customer_types')
    def validate_exempt_types(cls, v, values):
        """Ensure exempt types provided if has_exempt_sales."""
        if values.get('has_exempt_sales') and not v:
            raise ValueError("Exempt customer types required when has_exempt_sales is True")
        return v


class BusinessProfileCreate(BusinessProfileBase):
    """Schema for creating a business profile."""
    analysis_id: UUID


class BusinessProfileUpdate(BaseModel):
    """Schema for updating a business profile."""
    legal_business_name: Optional[str] = Field(None, min_length=1, max_length=255)
    doing_business_as: Optional[str] = Field(None, max_length=255)
    federal_ein: Optional[str] = Field(None, pattern=r'^\d{2}-?\d{7}$')

    business_structure: Optional[str] = Field(None, max_length=50)
    industry: Optional[str] = Field(None, max_length=100)
    naics_code: Optional[str] = Field(None, pattern=r'^\d{2,6}$')

    has_physical_presence: Optional[bool] = None
    has_employees: Optional[bool] = None
    has_inventory: Optional[bool] = None
    uses_marketplace_facilitators: Optional[bool] = None

    marketplace_facilitator_names: Optional[List[str]] = None

    sells_tangible_goods: Optional[bool] = None
    sells_digital_goods: Optional[bool] = None
    sells_services: Optional[bool] = None

    has_exempt_sales: Optional[bool] = None
    exempt_customer_types: Optional[List[str]] = None

    notes: Optional[str] = None


class BusinessProfileResponse(BusinessProfileBase):
    """Schema for business profile response."""
    profile_id: UUID
    analysis_id: UUID
    created_at: datetime
    updated_at: Optional[datetime]
    physical_locations: List[PhysicalLocationResponse] = []

    class Config:
        from_attributes = True


class BusinessProfileWithNexusStates(BusinessProfileResponse):
    """Schema for business profile with calculated nexus states."""
    physical_nexus_states: List[str] = Field(
        ...,
        description="List of state codes where physical nexus exists"
    )
