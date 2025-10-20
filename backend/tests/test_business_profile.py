"""
Tests for business profile functionality.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import date

from main import app
from database import Base, get_db
from models.user import User, UserRole
from models.tenant import Tenant
from models.analysis import Analysis, AnalysisStatus
from models.business_profile import BusinessProfile
from models.physical_location import PhysicalLocation, LocationType
from services.auth_service import create_access_token
from services.business_profile_service import business_profile_service


# In-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db_session():
    """Create a fresh database for each test."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db_session):
    """Create a test client with database dependency override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_tenant(db_session):
    """Create a test tenant."""
    tenant = Tenant(
        company_name="Test Company",
        subdomain="test"
    )
    db_session.add(tenant)
    db_session.commit()
    db_session.refresh(tenant)
    return tenant


@pytest.fixture
def test_user(db_session, test_tenant):
    """Create a test user."""
    user = User(
        tenant_id=test_tenant.tenant_id,
        email="test@example.com",
        password_hash="hashed_password",
        first_name="Test",
        last_name="User",
        role=UserRole.ADMIN
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user):
    """Create authorization headers."""
    token = create_access_token({"sub": test_user.email})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def test_analysis(db_session, test_user):
    """Create a test analysis."""
    analysis = Analysis(
        tenant_id=test_user.tenant_id,
        created_by=test_user.user_id,
        client_name="Test Client",
        period_start="2024-01-01",
        period_end="2024-12-31",
        status=AnalysisStatus.PENDING
    )
    db_session.add(analysis)
    db_session.commit()
    db_session.refresh(analysis)
    return analysis


# ==================== Business Profile Service Tests ====================

def test_get_physical_nexus_states_empty(db_session, test_analysis):
    """Test physical nexus with no locations."""
    profile = BusinessProfile(
        analysis_id=test_analysis.analysis_id,
        legal_business_name="Test Business",
        has_physical_presence=False
    )
    db_session.add(profile)
    db_session.commit()

    nexus_states = business_profile_service.get_physical_nexus_states(profile)
    assert nexus_states == []


def test_get_physical_nexus_states_with_locations(db_session, test_analysis):
    """Test physical nexus with multiple locations."""
    profile = BusinessProfile(
        analysis_id=test_analysis.analysis_id,
        legal_business_name="Test Business",
        has_physical_presence=True
    )
    db_session.add(profile)
    db_session.commit()
    db_session.refresh(profile)

    # Add locations in multiple states
    locations = [
        PhysicalLocation(
            profile_id=profile.profile_id,
            location_type=LocationType.OFFICE,
            address_line1="123 Main St",
            city="San Francisco",
            state="CA",
            zip_code="94102",
            established_date=date(2020, 1, 1)
        ),
        PhysicalLocation(
            profile_id=profile.profile_id,
            location_type=LocationType.WAREHOUSE,
            address_line1="456 Storage Rd",
            city="Los Angeles",
            state="CA",
            zip_code="90001",
            established_date=date(2021, 1, 1)
        ),
        PhysicalLocation(
            profile_id=profile.profile_id,
            location_type=LocationType.RETAIL_STORE,
            address_line1="789 Shop Ave",
            city="New York",
            state="NY",
            zip_code="10001",
            established_date=date(2022, 1, 1)
        )
    ]

    for loc in locations:
        db_session.add(loc)
    db_session.commit()
    db_session.refresh(profile)

    nexus_states = business_profile_service.get_physical_nexus_states(profile)
    assert sorted(nexus_states) == ['CA', 'NY']


def test_get_physical_nexus_states_with_closed_location(db_session, test_analysis):
    """Test physical nexus excludes closed locations."""
    profile = BusinessProfile(
        analysis_id=test_analysis.analysis_id,
        legal_business_name="Test Business",
        has_physical_presence=True
    )
    db_session.add(profile)
    db_session.commit()
    db_session.refresh(profile)

    # Add active and closed locations
    active_location = PhysicalLocation(
        profile_id=profile.profile_id,
        location_type=LocationType.OFFICE,
        address_line1="123 Main St",
        city="San Francisco",
        state="CA",
        zip_code="94102",
        established_date=date(2020, 1, 1)
    )

    closed_location = PhysicalLocation(
        profile_id=profile.profile_id,
        location_type=LocationType.OFFICE,
        address_line1="456 Old St",
        city="Austin",
        state="TX",
        zip_code="78701",
        established_date=date(2018, 1, 1),
        closed_date=date(2023, 12, 31)
    )

    db_session.add(active_location)
    db_session.add(closed_location)
    db_session.commit()
    db_session.refresh(profile)

    # As of today, TX location should be excluded
    nexus_states = business_profile_service.get_physical_nexus_states(profile)
    assert nexus_states == ['CA']


def test_determine_nexus_factors(db_session, test_analysis):
    """Test nexus factors determination."""
    profile = BusinessProfile(
        analysis_id=test_analysis.analysis_id,
        legal_business_name="Test Business",
        has_physical_presence=True,
        has_employees=True,
        has_inventory=True,
        uses_marketplace_facilitators=True,
        marketplace_facilitator_names=["Amazon", "eBay"],
        sells_tangible_goods=True,
        sells_digital_goods=False,
        has_exempt_sales=True,
        exempt_customer_types=["Resale", "Government"]
    )
    db_session.add(profile)
    db_session.commit()
    db_session.refresh(profile)

    factors = business_profile_service.determine_nexus_factors(profile)

    assert factors['has_physical_locations'] is True
    assert factors['has_employees'] is True
    assert factors['has_inventory'] is True
    assert factors['uses_marketplace_facilitators'] is True
    assert factors['marketplace_facilitators'] == ["Amazon", "eBay"]
    assert factors['sells_tangible_goods'] is True
    assert factors['has_exempt_sales'] is True


def test_validate_business_profile_completeness_missing_fields(db_session, test_analysis):
    """Test validation with missing fields."""
    profile = BusinessProfile(
        analysis_id=test_analysis.analysis_id,
        legal_business_name="Test Business",
        has_physical_presence=True,  # But no locations
        uses_marketplace_facilitators=True,  # But no names
        has_exempt_sales=True,  # But no types
        sells_tangible_goods=False,
        sells_digital_goods=False,
        sells_services=False  # Not selling anything
    )
    db_session.add(profile)
    db_session.commit()

    is_complete, missing = business_profile_service.validate_business_profile_completeness(profile)

    assert is_complete is False
    assert any('physical_locations' in field for field in missing)
    assert any('marketplace_facilitator_names' in field for field in missing)
    assert any('exempt_customer_types' in field for field in missing)
    assert any('sells_' in field for field in missing)


def test_has_remote_employees(db_session, test_analysis):
    """Test remote employee detection."""
    profile = BusinessProfile(
        analysis_id=test_analysis.analysis_id,
        legal_business_name="Test Business",
        has_physical_presence=True
    )
    db_session.add(profile)
    db_session.commit()
    db_session.refresh(profile)

    # Add remote employee location
    location = PhysicalLocation(
        profile_id=profile.profile_id,
        location_type=LocationType.REMOTE_EMPLOYEE,
        address_line1="123 Home St",
        city="Denver",
        state="CO",
        zip_code="80202"
    )
    db_session.add(location)
    db_session.commit()
    db_session.refresh(profile)

    assert business_profile_service.has_remote_employees(profile) is True


# ==================== Business Profile API Tests ====================

def test_create_business_profile(client, auth_headers, test_analysis):
    """Test creating a business profile."""
    data = {
        "analysis_id": str(test_analysis.analysis_id),
        "legal_business_name": "Test Corporation",
        "doing_business_as": "Test Corp",
        "federal_ein": "12-3456789",
        "business_structure": "LLC",
        "industry": "Software",
        "has_physical_presence": True,
        "has_employees": True,
        "sells_tangible_goods": True,
        "uses_marketplace_facilitators": False
    }

    response = client.post(
        "/api/v1/business-profile",
        json=data,
        headers=auth_headers
    )

    assert response.status_code == 201
    result = response.json()
    assert result['legal_business_name'] == "Test Corporation"
    assert result['federal_ein'] == "12-3456789"
    assert 'profile_id' in result


def test_create_business_profile_invalid_analysis(client, auth_headers):
    """Test creating profile for non-existent analysis."""
    data = {
        "analysis_id": "00000000-0000-0000-0000-000000000000",
        "legal_business_name": "Test Corporation",
        "sells_tangible_goods": True
    }

    response = client.post(
        "/api/v1/business-profile",
        json=data,
        headers=auth_headers
    )

    assert response.status_code == 404


def test_create_business_profile_duplicate(client, auth_headers, test_analysis, db_session):
    """Test creating duplicate profile for same analysis."""
    # Create first profile
    profile = BusinessProfile(
        analysis_id=test_analysis.analysis_id,
        legal_business_name="Existing Profile",
        sells_tangible_goods=True
    )
    db_session.add(profile)
    db_session.commit()

    # Try to create another
    data = {
        "analysis_id": str(test_analysis.analysis_id),
        "legal_business_name": "Test Corporation",
        "sells_tangible_goods": True
    }

    response = client.post(
        "/api/v1/business-profile",
        json=data,
        headers=auth_headers
    )

    assert response.status_code == 409


def test_get_business_profile(client, auth_headers, test_analysis, db_session):
    """Test retrieving a business profile."""
    profile = BusinessProfile(
        analysis_id=test_analysis.analysis_id,
        legal_business_name="Test Corporation",
        sells_tangible_goods=True
    )
    db_session.add(profile)
    db_session.commit()
    db_session.refresh(profile)

    response = client.get(
        f"/api/v1/business-profile/{profile.profile_id}",
        headers=auth_headers
    )

    assert response.status_code == 200
    result = response.json()
    assert result['legal_business_name'] == "Test Corporation"


def test_get_business_profile_by_analysis(client, auth_headers, test_analysis, db_session):
    """Test retrieving profile by analysis ID."""
    profile = BusinessProfile(
        analysis_id=test_analysis.analysis_id,
        legal_business_name="Test Corporation",
        sells_tangible_goods=True
    )
    db_session.add(profile)
    db_session.commit()

    response = client.get(
        f"/api/v1/business-profile/by-analysis/{test_analysis.analysis_id}",
        headers=auth_headers
    )

    assert response.status_code == 200
    result = response.json()
    assert result['legal_business_name'] == "Test Corporation"


def test_get_business_profile_with_nexus(client, auth_headers, test_analysis, db_session):
    """Test retrieving profile with nexus states."""
    profile = BusinessProfile(
        analysis_id=test_analysis.analysis_id,
        legal_business_name="Test Corporation",
        has_physical_presence=True,
        sells_tangible_goods=True
    )
    db_session.add(profile)
    db_session.commit()
    db_session.refresh(profile)

    # Add location
    location = PhysicalLocation(
        profile_id=profile.profile_id,
        location_type=LocationType.OFFICE,
        address_line1="123 Main St",
        city="San Francisco",
        state="CA",
        zip_code="94102"
    )
    db_session.add(location)
    db_session.commit()

    response = client.get(
        f"/api/v1/business-profile/{profile.profile_id}/with-nexus",
        headers=auth_headers
    )

    assert response.status_code == 200
    result = response.json()
    assert 'physical_nexus_states' in result
    assert 'CA' in result['physical_nexus_states']


def test_update_business_profile(client, auth_headers, test_analysis, db_session):
    """Test updating a business profile."""
    profile = BusinessProfile(
        analysis_id=test_analysis.analysis_id,
        legal_business_name="Test Corporation",
        sells_tangible_goods=True
    )
    db_session.add(profile)
    db_session.commit()
    db_session.refresh(profile)

    update_data = {
        "legal_business_name": "Updated Corporation",
        "has_employees": True
    }

    response = client.put(
        f"/api/v1/business-profile/{profile.profile_id}",
        json=update_data,
        headers=auth_headers
    )

    assert response.status_code == 200
    result = response.json()
    assert result['legal_business_name'] == "Updated Corporation"
    assert result['has_employees'] is True


def test_delete_business_profile(client, auth_headers, test_analysis, db_session):
    """Test deleting a business profile."""
    profile = BusinessProfile(
        analysis_id=test_analysis.analysis_id,
        legal_business_name="Test Corporation",
        sells_tangible_goods=True
    )
    db_session.add(profile)
    db_session.commit()
    db_session.refresh(profile)

    response = client.delete(
        f"/api/v1/business-profile/{profile.profile_id}",
        headers=auth_headers
    )

    assert response.status_code == 204

    # Verify deletion
    deleted = db_session.query(BusinessProfile).filter(
        BusinessProfile.profile_id == profile.profile_id
    ).first()
    assert deleted is None


# ==================== Physical Location API Tests ====================

def test_add_physical_location(client, auth_headers, test_analysis, db_session):
    """Test adding a physical location."""
    profile = BusinessProfile(
        analysis_id=test_analysis.analysis_id,
        legal_business_name="Test Corporation",
        has_physical_presence=False,  # Will be updated to True
        sells_tangible_goods=True
    )
    db_session.add(profile)
    db_session.commit()
    db_session.refresh(profile)

    location_data = {
        "location_type": "office",
        "address_line1": "123 Main St",
        "city": "San Francisco",
        "state": "CA",
        "zip_code": "94102",
        "established_date": "2020-01-01"
    }

    response = client.post(
        f"/api/v1/business-profile/{profile.profile_id}/locations",
        json=location_data,
        headers=auth_headers
    )

    assert response.status_code == 201
    result = response.json()
    assert result['location_type'] == "office"
    assert result['state'] == "CA"

    # Verify has_physical_presence updated
    db_session.refresh(profile)
    assert profile.has_physical_presence is True


def test_get_physical_locations(client, auth_headers, test_analysis, db_session):
    """Test retrieving all physical locations."""
    profile = BusinessProfile(
        analysis_id=test_analysis.analysis_id,
        legal_business_name="Test Corporation",
        has_physical_presence=True,
        sells_tangible_goods=True
    )
    db_session.add(profile)
    db_session.commit()
    db_session.refresh(profile)

    # Add multiple locations
    locations = [
        PhysicalLocation(
            profile_id=profile.profile_id,
            location_type=LocationType.OFFICE,
            address_line1="123 Main St",
            city="San Francisco",
            state="CA",
            zip_code="94102"
        ),
        PhysicalLocation(
            profile_id=profile.profile_id,
            location_type=LocationType.WAREHOUSE,
            address_line1="456 Storage Rd",
            city="Los Angeles",
            state="CA",
            zip_code="90001"
        )
    ]
    for loc in locations:
        db_session.add(loc)
    db_session.commit()

    response = client.get(
        f"/api/v1/business-profile/{profile.profile_id}/locations",
        headers=auth_headers
    )

    assert response.status_code == 200
    result = response.json()
    assert len(result) == 2


def test_update_physical_location(client, auth_headers, test_analysis, db_session):
    """Test updating a physical location."""
    profile = BusinessProfile(
        analysis_id=test_analysis.analysis_id,
        legal_business_name="Test Corporation",
        has_physical_presence=True,
        sells_tangible_goods=True
    )
    db_session.add(profile)
    db_session.commit()
    db_session.refresh(profile)

    location = PhysicalLocation(
        profile_id=profile.profile_id,
        location_type=LocationType.OFFICE,
        address_line1="123 Main St",
        city="San Francisco",
        state="CA",
        zip_code="94102"
    )
    db_session.add(location)
    db_session.commit()
    db_session.refresh(location)

    update_data = {
        "city": "Oakland",
        "zip_code": "94601"
    }

    response = client.put(
        f"/api/v1/business-profile/{profile.profile_id}/locations/{location.location_id}",
        json=update_data,
        headers=auth_headers
    )

    assert response.status_code == 200
    result = response.json()
    assert result['city'] == "Oakland"
    assert result['zip_code'] == "94601"


def test_delete_physical_location(client, auth_headers, test_analysis, db_session):
    """Test deleting a physical location."""
    profile = BusinessProfile(
        analysis_id=test_analysis.analysis_id,
        legal_business_name="Test Corporation",
        has_physical_presence=True,
        sells_tangible_goods=True
    )
    db_session.add(profile)
    db_session.commit()
    db_session.refresh(profile)

    location = PhysicalLocation(
        profile_id=profile.profile_id,
        location_type=LocationType.OFFICE,
        address_line1="123 Main St",
        city="San Francisco",
        state="CA",
        zip_code="94102"
    )
    db_session.add(location)
    db_session.commit()
    db_session.refresh(location)

    response = client.delete(
        f"/api/v1/business-profile/{profile.profile_id}/locations/{location.location_id}",
        headers=auth_headers
    )

    assert response.status_code == 204

    # Verify deletion
    deleted = db_session.query(PhysicalLocation).filter(
        PhysicalLocation.location_id == location.location_id
    ).first()
    assert deleted is None


def test_get_nexus_factors(client, auth_headers, test_analysis, db_session):
    """Test getting nexus factors."""
    profile = BusinessProfile(
        analysis_id=test_analysis.analysis_id,
        legal_business_name="Test Corporation",
        has_physical_presence=True,
        has_employees=True,
        uses_marketplace_facilitators=True,
        marketplace_facilitator_names=["Amazon"],
        sells_tangible_goods=True
    )
    db_session.add(profile)
    db_session.commit()
    db_session.refresh(profile)

    response = client.get(
        f"/api/v1/business-profile/{profile.profile_id}/nexus-factors",
        headers=auth_headers
    )

    assert response.status_code == 200
    result = response.json()
    assert result['has_physical_locations'] is True
    assert result['has_employees'] is True
    assert result['uses_marketplace_facilitators'] is True
    assert 'Amazon' in result['marketplace_facilitators']


def test_validate_profile_completeness(client, auth_headers, test_analysis, db_session):
    """Test profile completeness validation."""
    profile = BusinessProfile(
        analysis_id=test_analysis.analysis_id,
        legal_business_name="Test Corporation",
        business_structure="LLC",
        sells_tangible_goods=True
    )
    db_session.add(profile)
    db_session.commit()
    db_session.refresh(profile)

    response = client.get(
        f"/api/v1/business-profile/{profile.profile_id}/validation",
        headers=auth_headers
    )

    assert response.status_code == 200
    result = response.json()
    assert 'is_complete' in result
    assert 'missing_fields' in result
