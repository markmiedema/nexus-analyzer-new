"""
Business profile API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from database import get_db
from models.user import User
from models.business_profile import BusinessProfile
from models.physical_location import PhysicalLocation
from models.analysis import Analysis
from dependencies.auth import get_current_user
from schemas.business_profile import (
    BusinessProfileCreate,
    BusinessProfileUpdate,
    BusinessProfileResponse,
    BusinessProfileWithNexusStates,
    PhysicalLocationCreate,
    PhysicalLocationUpdate,
    PhysicalLocationResponse
)
from services.business_profile_service import business_profile_service

router = APIRouter()


@router.post("", response_model=BusinessProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_business_profile(
    profile_data: BusinessProfileCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create business profile for an analysis.

    - **analysis_id**: UUID of the analysis
    - **legal_business_name**: Legal name of the business (required)
    - **business_structure**: LLC, Corp, Partnership, etc.
    - **has_physical_presence**: Whether business has physical locations
    - **uses_marketplace_facilitators**: Whether business uses Amazon, eBay, etc.
    - **sells_tangible_goods**: Whether business sells physical products
    """

    # Verify analysis exists and belongs to user's tenant
    analysis = db.query(Analysis).filter(
        Analysis.analysis_id == profile_data.analysis_id,
        Analysis.tenant_id == current_user.tenant_id
    ).first()

    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found"
        )

    # Check if profile already exists for this analysis
    existing_profile = db.query(BusinessProfile).filter(
        BusinessProfile.analysis_id == profile_data.analysis_id
    ).first()

    if existing_profile:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Business profile already exists for this analysis"
        )

    # Create business profile
    profile = BusinessProfile(
        **profile_data.model_dump()
    )

    db.add(profile)
    db.commit()
    db.refresh(profile)

    return profile


@router.get("/{profile_id}", response_model=BusinessProfileResponse)
async def get_business_profile(
    profile_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve business profile by ID.

    Returns business profile with all physical locations.
    """

    profile = db.query(BusinessProfile).filter(
        BusinessProfile.profile_id == profile_id
    ).first()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business profile not found"
        )

    # Verify tenant access through analysis
    analysis = db.query(Analysis).filter(
        Analysis.analysis_id == profile.analysis_id,
        Analysis.tenant_id == current_user.tenant_id
    ).first()

    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business profile not found"
        )

    return profile


@router.get("/by-analysis/{analysis_id}", response_model=BusinessProfileResponse)
async def get_business_profile_by_analysis(
    analysis_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve business profile by analysis ID.
    """

    # Verify analysis exists and belongs to user's tenant
    analysis = db.query(Analysis).filter(
        Analysis.analysis_id == analysis_id,
        Analysis.tenant_id == current_user.tenant_id
    ).first()

    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found"
        )

    # Get business profile
    profile = db.query(BusinessProfile).filter(
        BusinessProfile.analysis_id == analysis_id
    ).first()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business profile not found for this analysis"
        )

    return profile


@router.get("/{profile_id}/with-nexus", response_model=BusinessProfileWithNexusStates)
async def get_business_profile_with_nexus(
    profile_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve business profile with calculated physical nexus states.

    Returns business profile with additional field 'physical_nexus_states'
    containing list of state codes where physical nexus exists.
    """

    profile = db.query(BusinessProfile).filter(
        BusinessProfile.profile_id == profile_id
    ).first()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business profile not found"
        )

    # Verify tenant access
    analysis = db.query(Analysis).filter(
        Analysis.analysis_id == profile.analysis_id,
        Analysis.tenant_id == current_user.tenant_id
    ).first()

    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business profile not found"
        )

    # Calculate physical nexus states
    nexus_states = business_profile_service.get_physical_nexus_states(profile)

    # Convert to dict and add nexus states
    profile_dict = BusinessProfileResponse.from_orm(profile).model_dump()
    profile_dict['physical_nexus_states'] = nexus_states

    return profile_dict


@router.put("/{profile_id}", response_model=BusinessProfileResponse)
async def update_business_profile(
    profile_id: UUID,
    profile_data: BusinessProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update business profile.

    Only provided fields will be updated.
    """

    profile = db.query(BusinessProfile).filter(
        BusinessProfile.profile_id == profile_id
    ).first()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business profile not found"
        )

    # Verify tenant access
    analysis = db.query(Analysis).filter(
        Analysis.analysis_id == profile.analysis_id,
        Analysis.tenant_id == current_user.tenant_id
    ).first()

    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business profile not found"
        )

    # Update fields
    update_data = profile_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(profile, field, value)

    db.commit()
    db.refresh(profile)

    return profile


@router.delete("/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_business_profile(
    profile_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete business profile.

    This will also delete all associated physical locations (cascade delete).
    """

    profile = db.query(BusinessProfile).filter(
        BusinessProfile.profile_id == profile_id
    ).first()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business profile not found"
        )

    # Verify tenant access
    analysis = db.query(Analysis).filter(
        Analysis.analysis_id == profile.analysis_id,
        Analysis.tenant_id == current_user.tenant_id
    ).first()

    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business profile not found"
        )

    db.delete(profile)
    db.commit()


# ==================== Physical Location Endpoints ====================

@router.post("/{profile_id}/locations", response_model=PhysicalLocationResponse, status_code=status.HTTP_201_CREATED)
async def add_physical_location(
    profile_id: UUID,
    location_data: PhysicalLocationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Add physical location to business profile.

    - **location_type**: office, warehouse, retail_store, manufacturing, remote_employee, other
    - **state**: Two-letter state code (e.g., CA, NY)
    - **established_date**: When location was established (optional)
    """

    # Verify profile exists and user has access
    profile = db.query(BusinessProfile).filter(
        BusinessProfile.profile_id == profile_id
    ).first()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business profile not found"
        )

    # Verify tenant access
    analysis = db.query(Analysis).filter(
        Analysis.analysis_id == profile.analysis_id,
        Analysis.tenant_id == current_user.tenant_id
    ).first()

    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business profile not found"
        )

    # Create location
    location = PhysicalLocation(
        profile_id=profile_id,
        **location_data.model_dump()
    )

    db.add(location)

    # Update has_physical_presence flag if needed
    if not profile.has_physical_presence:
        profile.has_physical_presence = True

    db.commit()
    db.refresh(location)

    return location


@router.get("/{profile_id}/locations", response_model=List[PhysicalLocationResponse])
async def get_physical_locations(
    profile_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all physical locations for a business profile.
    """

    # Verify profile exists and user has access
    profile = db.query(BusinessProfile).filter(
        BusinessProfile.profile_id == profile_id
    ).first()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business profile not found"
        )

    # Verify tenant access
    analysis = db.query(Analysis).filter(
        Analysis.analysis_id == profile.analysis_id,
        Analysis.tenant_id == current_user.tenant_id
    ).first()

    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business profile not found"
        )

    locations = db.query(PhysicalLocation).filter(
        PhysicalLocation.profile_id == profile_id
    ).all()

    return locations


@router.put("/{profile_id}/locations/{location_id}", response_model=PhysicalLocationResponse)
async def update_physical_location(
    profile_id: UUID,
    location_id: UUID,
    location_data: PhysicalLocationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update physical location.
    """

    # Verify profile exists and user has access
    profile = db.query(BusinessProfile).filter(
        BusinessProfile.profile_id == profile_id
    ).first()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business profile not found"
        )

    # Verify tenant access
    analysis = db.query(Analysis).filter(
        Analysis.analysis_id == profile.analysis_id,
        Analysis.tenant_id == current_user.tenant_id
    ).first()

    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business profile not found"
        )

    # Get location
    location = db.query(PhysicalLocation).filter(
        PhysicalLocation.location_id == location_id,
        PhysicalLocation.profile_id == profile_id
    ).first()

    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Physical location not found"
        )

    # Update fields
    update_data = location_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(location, field, value)

    db.commit()
    db.refresh(location)

    return location


@router.delete("/{profile_id}/locations/{location_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_physical_location(
    profile_id: UUID,
    location_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete physical location.
    """

    # Verify profile exists and user has access
    profile = db.query(BusinessProfile).filter(
        BusinessProfile.profile_id == profile_id
    ).first()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business profile not found"
        )

    # Verify tenant access
    analysis = db.query(Analysis).filter(
        Analysis.analysis_id == profile.analysis_id,
        Analysis.tenant_id == current_user.tenant_id
    ).first()

    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business profile not found"
        )

    # Get location
    location = db.query(PhysicalLocation).filter(
        PhysicalLocation.location_id == location_id,
        PhysicalLocation.profile_id == profile_id
    ).first()

    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Physical location not found"
        )

    db.delete(location)
    db.commit()


@router.get("/{profile_id}/nexus-factors")
async def get_nexus_factors(
    profile_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get nexus factors analysis for business profile.

    Returns detailed information about physical presence, employees,
    inventory, marketplace facilitators, and product types.
    """

    profile = db.query(BusinessProfile).filter(
        BusinessProfile.profile_id == profile_id
    ).first()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business profile not found"
        )

    # Verify tenant access
    analysis = db.query(Analysis).filter(
        Analysis.analysis_id == profile.analysis_id,
        Analysis.tenant_id == current_user.tenant_id
    ).first()

    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business profile not found"
        )

    # Get nexus factors
    factors = business_profile_service.determine_nexus_factors(profile)

    return factors


@router.get("/{profile_id}/validation")
async def validate_profile_completeness(
    profile_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Validate business profile completeness.

    Returns validation status and list of missing/recommended fields.
    """

    profile = db.query(BusinessProfile).filter(
        BusinessProfile.profile_id == profile_id
    ).first()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business profile not found"
        )

    # Verify tenant access
    analysis = db.query(Analysis).filter(
        Analysis.analysis_id == profile.analysis_id,
        Analysis.tenant_id == current_user.tenant_id
    ).first()

    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business profile not found"
        )

    # Validate completeness
    is_complete, missing_fields = business_profile_service.validate_business_profile_completeness(profile)

    return {
        "is_complete": is_complete,
        "missing_fields": missing_fields,
        "profile_id": str(profile_id)
    }
