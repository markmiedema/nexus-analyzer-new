"""
Pytest configuration and shared fixtures.

This module provides reusable fixtures for testing the application.
"""

import sys
from pathlib import Path

# Add parent directory to path to allow imports
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import uuid
from typing import Generator, Dict

from main import app
from database import Base, get_db
from models.tenant import Tenant, TenantStatus, SubscriptionPlan
from models.user import User, UserRole
from services.auth_service import auth_service
from config import settings

# Test database URL (in-memory SQLite for fast tests)
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

# Create test engine
test_engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Create test session factory
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


# ============================================================================
# Database Fixtures
# ============================================================================

@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    """
    Create a fresh database for each test.

    Yields:
        Session: SQLAlchemy database session
    """
    # Create all tables
    Base.metadata.create_all(bind=test_engine)

    # Create session
    db_session = TestingSessionLocal()

    try:
        yield db_session
    finally:
        db_session.close()
        # Drop all tables after test
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db: Session) -> Generator[TestClient, None, None]:
    """
    Create a test client with database dependency override.

    Args:
        db: Database session fixture

    Yields:
        TestClient: FastAPI test client
    """
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


# ============================================================================
# Tenant Fixtures
# ============================================================================

@pytest.fixture
def test_tenant(db: Session) -> Tenant:
    """
    Create a test tenant.

    Args:
        db: Database session

    Returns:
        Tenant: Test tenant
    """
    tenant = Tenant(
        tenant_id=str(uuid.uuid4()),
        company_name="Test Company",
        subdomain="test",
        status=TenantStatus.ACTIVE,
        subscription_plan=SubscriptionPlan.PROFESSIONAL
    )
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return tenant


@pytest.fixture
def demo_tenant(db: Session) -> Tenant:
    """
    Create a demo tenant (matches production demo tenant).

    Args:
        db: Database session

    Returns:
        Tenant: Demo tenant
    """
    tenant = Tenant(
        tenant_id=str(uuid.uuid4()),
        company_name="Demo Company",
        subdomain="demo",
        status=TenantStatus.TRIAL,
        subscription_plan=SubscriptionPlan.FREE
    )
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return tenant


# ============================================================================
# User Fixtures
# ============================================================================

@pytest.fixture
def test_user(db: Session, test_tenant: Tenant) -> User:
    """
    Create a test user (admin role).

    Args:
        db: Database session
        test_tenant: Test tenant

    Returns:
        User: Test user with admin role
    """
    user = User(
        user_id=str(uuid.uuid4()),
        tenant_id=test_tenant.tenant_id,
        email="test@example.com",
        password_hash=auth_service.hash_password("testpass123"),
        first_name="Test",
        last_name="User",
        role=UserRole.ADMIN,
        is_active=True,
        email_verified=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def analyst_user(db: Session, test_tenant: Tenant) -> User:
    """
    Create an analyst user.

    Args:
        db: Database session
        test_tenant: Test tenant

    Returns:
        User: Test user with analyst role
    """
    user = User(
        user_id=str(uuid.uuid4()),
        tenant_id=test_tenant.tenant_id,
        email="analyst@example.com",
        password_hash=auth_service.hash_password("analystpass123"),
        first_name="Analyst",
        last_name="User",
        role=UserRole.ANALYST,
        is_active=True,
        email_verified=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def viewer_user(db: Session, test_tenant: Tenant) -> User:
    """
    Create a viewer user (read-only).

    Args:
        db: Database session
        test_tenant: Test tenant

    Returns:
        User: Test user with viewer role
    """
    user = User(
        user_id=str(uuid.uuid4()),
        tenant_id=test_tenant.tenant_id,
        email="viewer@example.com",
        password_hash=auth_service.hash_password("viewerpass123"),
        first_name="Viewer",
        last_name="User",
        role=UserRole.VIEWER,
        is_active=True,
        email_verified=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def inactive_user(db: Session, test_tenant: Tenant) -> User:
    """
    Create an inactive user (for testing access control).

    Args:
        db: Database session
        test_tenant: Test tenant

    Returns:
        User: Inactive user
    """
    user = User(
        user_id=str(uuid.uuid4()),
        tenant_id=test_tenant.tenant_id,
        email="inactive@example.com",
        password_hash=auth_service.hash_password("inactivepass123"),
        first_name="Inactive",
        last_name="User",
        role=UserRole.VIEWER,
        is_active=False,
        email_verified=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# ============================================================================
# Authentication Fixtures
# ============================================================================

@pytest.fixture
def auth_headers(test_user: User) -> Dict[str, str]:
    """
    Create authentication headers with valid JWT token.

    Args:
        test_user: Test user

    Returns:
        dict: Headers with Authorization bearer token
    """
    token_data = auth_service.create_tokens_for_user(
        user_id=str(test_user.user_id),
        tenant_id=str(test_user.tenant_id),
        email=test_user.email,
        role=test_user.role.value
    )

    return {
        "Authorization": f"Bearer {token_data['access_token']}"
    }


@pytest.fixture
def analyst_auth_headers(analyst_user: User) -> Dict[str, str]:
    """
    Create authentication headers for analyst user.

    Args:
        analyst_user: Analyst user

    Returns:
        dict: Headers with Authorization bearer token
    """
    token_data = auth_service.create_tokens_for_user(
        user_id=str(analyst_user.user_id),
        tenant_id=str(analyst_user.tenant_id),
        email=analyst_user.email,
        role=analyst_user.role.value
    )

    return {
        "Authorization": f"Bearer {token_data['access_token']}"
    }


@pytest.fixture
def viewer_auth_headers(viewer_user: User) -> Dict[str, str]:
    """
    Create authentication headers for viewer user.

    Args:
        viewer_user: Viewer user

    Returns:
        dict: Headers with Authorization bearer token
    """
    token_data = auth_service.create_tokens_for_user(
        user_id=str(viewer_user.user_id),
        tenant_id=str(viewer_user.tenant_id),
        email=viewer_user.email,
        role=viewer_user.role.value
    )

    return {
        "Authorization": f"Bearer {token_data['access_token']}"
    }


# ============================================================================
# Helper Functions
# ============================================================================

@pytest.fixture
def login_user(client: TestClient):
    """
    Helper function to login a user via API.

    Args:
        client: Test client

    Returns:
        function: Login function that returns response
    """
    def _login(email: str, password: str, tenant_subdomain: str = "test"):
        """Login a user and return the response."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": email,
                "password": password,
                "tenant_subdomain": tenant_subdomain
            }
        )
        return response

    return _login


@pytest.fixture
def create_user_via_api(client: TestClient):
    """
    Helper function to create a user via registration API.

    Args:
        client: Test client

    Returns:
        function: Registration function
    """
    def _create_user(
        email: str,
        password: str,
        first_name: str = "Test",
        last_name: str = "User",
        tenant_subdomain: str = "test"
    ):
        """Register a new user and return the response."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "password": password,
                "first_name": first_name,
                "last_name": last_name,
                "tenant_subdomain": tenant_subdomain
            }
        )
        return response

    return _create_user
