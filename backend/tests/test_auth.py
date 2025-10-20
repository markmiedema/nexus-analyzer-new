"""
Tests for authentication endpoints and services.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from database import Base, get_db
from models.tenant import Tenant, TenantStatus, SubscriptionPlan
from models.user import User, UserRole
from services.auth_service import auth_service
import uuid

# Create in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override dependency
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(scope="function")
def db_session():
    """Create fresh database for each test."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_tenant(db_session):
    """Create a test tenant."""
    tenant = Tenant(
        tenant_id=uuid.uuid4(),
        company_name="Test Company",
        subdomain="testco",
        subscription_plan=SubscriptionPlan.FREE,
        status=TenantStatus.ACTIVE
    )
    db_session.add(tenant)
    db_session.commit()
    db_session.refresh(tenant)
    return tenant


@pytest.fixture
def test_user(db_session, test_tenant):
    """Create a test user."""
    hashed_password = auth_service.hash_password("TestPassword123")
    user = User(
        user_id=uuid.uuid4(),
        tenant_id=test_tenant.tenant_id,
        email="test@example.com",
        password_hash=hashed_password,
        first_name="Test",
        last_name="User",
        role=UserRole.ADMIN,
        is_active="true",
        email_verified="false"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


class TestAuthService:
    """Test authentication service functions."""

    def test_hash_password(self):
        """Test password hashing."""
        password = "TestPassword123"
        hashed = auth_service.hash_password(password)

        assert hashed != password
        assert len(hashed) > 0

    def test_verify_password(self):
        """Test password verification."""
        password = "TestPassword123"
        hashed = auth_service.hash_password(password)

        assert auth_service.verify_password(password, hashed) is True
        assert auth_service.verify_password("WrongPassword", hashed) is False

    def test_create_access_token(self):
        """Test JWT token creation."""
        data = {"sub": "test-user-id", "email": "test@example.com"}
        token = auth_service.create_access_token(data)

        assert token is not None
        assert len(token) > 0

    def test_decode_access_token(self):
        """Test JWT token decoding."""
        data = {"sub": "test-user-id", "email": "test@example.com"}
        token = auth_service.create_access_token(data)

        decoded = auth_service.decode_access_token(token)

        assert decoded is not None
        assert decoded["sub"] == "test-user-id"
        assert decoded["email"] == "test@example.com"

    def test_decode_invalid_token(self):
        """Test decoding invalid token."""
        decoded = auth_service.decode_access_token("invalid-token")
        assert decoded is None


class TestRegisterEndpoint:
    """Test user registration endpoint."""

    def test_register_success(self, db_session, test_tenant):
        """Test successful user registration."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "NewPassword123",
                "first_name": "New",
                "last_name": "User",
                "tenant_subdomain": "testco"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["first_name"] == "New"
        assert data["last_name"] == "User"
        assert "user_id" in data

    def test_register_duplicate_email(self, db_session, test_user):
        """Test registration with duplicate email."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",  # Already exists
                "password": "NewPassword123",
                "first_name": "New",
                "last_name": "User",
                "tenant_subdomain": "testco"
            }
        )

        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    def test_register_weak_password(self, db_session, test_tenant):
        """Test registration with weak password."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "weak",  # Too weak
                "first_name": "New",
                "last_name": "User",
                "tenant_subdomain": "testco"
            }
        )

        assert response.status_code == 422  # Validation error


class TestLoginEndpoint:
    """Test user login endpoint."""

    def test_login_success(self, db_session, test_user):
        """Test successful login."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "TestPassword123",
                "tenant_subdomain": "testco"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, db_session, test_user):
        """Test login with wrong password."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "WrongPassword123",
                "tenant_subdomain": "testco"
            }
        )

        assert response.status_code == 401
        assert "invalid credentials" in response.json()["detail"].lower()

    def test_login_nonexistent_user(self, db_session, test_tenant):
        """Test login with non-existent user."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "Password123",
                "tenant_subdomain": "testco"
            }
        )

        assert response.status_code == 401


class TestMeEndpoint:
    """Test current user info endpoint."""

    def test_get_me_success(self, db_session, test_user):
        """Test getting current user info."""
        # First login to get token
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "TestPassword123",
                "tenant_subdomain": "testco"
            }
        )
        token = login_response.json()["access_token"]

        # Get current user info
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["first_name"] == "Test"

    def test_get_me_no_token(self):
        """Test getting current user info without token."""
        response = client.get("/api/v1/auth/me")

        assert response.status_code == 403  # No auth header


class TestUserManagement:
    """Test user management endpoints."""

    def test_list_users(self, db_session, test_user):
        """Test listing users."""
        # Login first
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "TestPassword123",
                "tenant_subdomain": "testco"
            }
        )
        token = login_response.json()["access_token"]

        # List users
        response = client.get(
            "/api/v1/users",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1  # At least the test user


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
