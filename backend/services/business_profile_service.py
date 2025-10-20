"""
Business profile service for managing business profiles and physical locations.
"""

from sqlalchemy.orm import Session
from typing import List, Set, Optional
from datetime import date
import logging

from models.business_profile import BusinessProfile
from models.physical_location import PhysicalLocation, LocationType

logger = logging.getLogger(__name__)


class BusinessProfileService:
    """Service for business profile operations."""

    @staticmethod
    def get_physical_nexus_states(
        business_profile: BusinessProfile,
        as_of_date: Optional[date] = None
    ) -> List[str]:
        """
        Extract list of states where physical nexus exists.

        Args:
            business_profile: BusinessProfile instance
            as_of_date: Date to check for active locations (defaults to today)

        Returns:
            List of two-letter state codes

        Note:
            Physical nexus is established when a business has:
            - Office
            - Warehouse/inventory storage
            - Retail store
            - Manufacturing facility
            - Remote employees (in some states)
        """
        if not business_profile.has_physical_presence:
            return []

        if as_of_date is None:
            as_of_date = date.today()

        nexus_states: Set[str] = set()

        for location in business_profile.physical_locations:
            # Check if location was active on the as_of_date
            if location.established_date and location.established_date > as_of_date:
                # Location not yet established
                continue

            if location.closed_date and location.closed_date <= as_of_date:
                # Location already closed
                continue

            # Add state to nexus states
            nexus_states.add(location.state.upper())
            logger.debug(
                f"Physical nexus in {location.state}: "
                f"{location.location_type.value} at {location.city}"
            )

        return sorted(list(nexus_states))

    @staticmethod
    def get_physical_nexus_details(
        business_profile: BusinessProfile,
        as_of_date: Optional[date] = None
    ) -> dict:
        """
        Get detailed physical nexus information by state.

        Args:
            business_profile: BusinessProfile instance
            as_of_date: Date to check for active locations

        Returns:
            Dict mapping state codes to location details
        """
        if not business_profile.has_physical_presence:
            return {}

        if as_of_date is None:
            as_of_date = date.today()

        nexus_details = {}

        for location in business_profile.physical_locations:
            # Check if location was active
            if location.established_date and location.established_date > as_of_date:
                continue
            if location.closed_date and location.closed_date <= as_of_date:
                continue

            state = location.state.upper()

            if state not in nexus_details:
                nexus_details[state] = {
                    'state': state,
                    'locations': []
                }

            nexus_details[state]['locations'].append({
                'location_id': str(location.location_id),
                'location_type': location.location_type.value,
                'city': location.city,
                'established_date': location.established_date,
                'description': location.description
            })

        return nexus_details

    @staticmethod
    def determine_nexus_factors(business_profile: BusinessProfile) -> dict:
        """
        Determine various nexus factors for the business.

        Args:
            business_profile: BusinessProfile instance

        Returns:
            Dict with nexus factor analysis
        """
        factors = {
            'has_physical_locations': business_profile.has_physical_presence,
            'location_count': len(business_profile.physical_locations) if business_profile.has_physical_presence else 0,
            'physical_states': [],
            'has_employees': business_profile.has_employees,
            'has_inventory': business_profile.has_inventory,
            'uses_marketplace_facilitators': business_profile.uses_marketplace_facilitators,
            'marketplace_facilitators': business_profile.marketplace_facilitator_names or [],
            'sells_tangible_goods': business_profile.sells_tangible_goods,
            'sells_digital_goods': business_profile.sells_digital_goods,
            'sells_services': business_profile.sells_services,
            'has_exempt_sales': business_profile.has_exempt_sales,
            'exempt_types': business_profile.exempt_customer_types or []
        }

        if business_profile.has_physical_presence:
            factors['physical_states'] = BusinessProfileService.get_physical_nexus_states(
                business_profile
            )

        return factors

    @staticmethod
    def validate_business_profile_completeness(
        business_profile: BusinessProfile
    ) -> tuple[bool, List[str]]:
        """
        Validate that business profile has all necessary information.

        Args:
            business_profile: BusinessProfile instance

        Returns:
            Tuple of (is_complete, missing_fields)
        """
        missing = []

        # Required fields
        if not business_profile.legal_business_name:
            missing.append("legal_business_name")

        # Business structure recommended
        if not business_profile.business_structure:
            missing.append("business_structure (recommended)")

        # If has physical presence, must have locations
        if business_profile.has_physical_presence and not business_profile.physical_locations:
            missing.append("physical_locations (has_physical_presence is True)")

        # If uses marketplace facilitators, must specify which ones
        if business_profile.uses_marketplace_facilitators and not business_profile.marketplace_facilitator_names:
            missing.append("marketplace_facilitator_names")

        # If has exempt sales, must specify types
        if business_profile.has_exempt_sales and not business_profile.exempt_customer_types:
            missing.append("exempt_customer_types")

        # Must sell something
        if not (business_profile.sells_tangible_goods or
                business_profile.sells_digital_goods or
                business_profile.sells_services):
            missing.append("must specify at least one: sells_tangible_goods, sells_digital_goods, or sells_services")

        is_complete = len(missing) == 0
        return is_complete, missing

    @staticmethod
    def get_location_types_by_state(
        business_profile: BusinessProfile
    ) -> dict:
        """
        Group locations by state with their types.

        Args:
            business_profile: BusinessProfile instance

        Returns:
            Dict mapping state codes to list of location types
        """
        state_locations = {}

        for location in business_profile.physical_locations:
            state = location.state.upper()

            if state not in state_locations:
                state_locations[state] = []

            state_locations[state].append({
                'type': location.location_type.value,
                'city': location.city,
                'established': location.established_date,
                'closed': location.closed_date
            })

        return state_locations

    @staticmethod
    def has_remote_employees(business_profile: BusinessProfile) -> bool:
        """
        Check if business has remote employees.

        Args:
            business_profile: BusinessProfile instance

        Returns:
            bool: True if remote employees exist
        """
        return any(
            loc.location_type == LocationType.REMOTE_EMPLOYEE
            for loc in business_profile.physical_locations
        )

    @staticmethod
    def has_inventory_storage(business_profile: BusinessProfile) -> bool:
        """
        Check if business has inventory storage locations.

        Args:
            business_profile: BusinessProfile instance

        Returns:
            bool: True if warehouse/inventory locations exist
        """
        return any(
            loc.location_type == LocationType.WAREHOUSE
            for loc in business_profile.physical_locations
        )

    @staticmethod
    def get_states_with_remote_employees(
        business_profile: BusinessProfile
    ) -> List[str]:
        """
        Get list of states where remote employees are located.

        Args:
            business_profile: BusinessProfile instance

        Returns:
            List of state codes
        """
        return sorted(list(set(
            loc.state.upper()
            for loc in business_profile.physical_locations
            if loc.location_type == LocationType.REMOTE_EMPLOYEE
        )))


# Create global instance
business_profile_service = BusinessProfileService()
