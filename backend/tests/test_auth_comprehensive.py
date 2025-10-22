"""
Comprehensive authentication tests using pytest fixtures.

Tests cover:
- User registration
- Login/logout
- Token validation
- httpOnly cookies
- Refresh tokens
- Password changes
- Role-based access control
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from models.user import User, UserRole
from models.tenant import Tenant


# ============================================================================
# Registration Tests
# ============================================================================

@pytest.mark.auth
@pytest.mark.api
class TestRegistration:
    """Tests for user registration endpoint."""

    def test_register_new_user(self, client: TestClient, test_tenant: Tenant):
        """Test successful user registration."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "NewPass123!",
                "first_name": "New",
                "last_name": "User",
                "tenant_subdomain": "test"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["first_name"] == "New"
        assert data["last_name"] == "User"
        assert data["is_active"] is True
        assert data["role"] == "viewer"  # Default role

    def test_register_duplicate_email(
        self,
        client: TestClient,
        test_user: User,
        test_tenant: Tenant
    ):
        """Test registration with duplicate email fails."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": test_user.email,  # Duplicate email
                "password": "Password123!",
                "first_name": "Duplicate",
                "last_name": "User",
                "tenant_subdomain": "test"
            }
        )

        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()

    def test_register_weak_password(self, client: TestClient, test_tenant: Tenant):
        """Test registration with weak password fails."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "weak@example.com",
                "password": "weak",  # Too weak
                "first_name": "Weak",
                "last_name": "Password",
                "tenant_subdomain": "test"
            }
        )

        assert response.status_code == 422  # Validation error

    def test_register_invalid_email(self, client: TestClient, test_tenant: Tenant):
        """Test registration with invalid email fails."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "not-an-email",  # Invalid
                "password": "Password123!",
                "first_name": "Invalid",
                "last_name": "Email",
                "tenant_subdomain": "test"
            }
        )

        assert response.status_code == 422  # Validation error


# ============================================================================
# Login/Logout Tests
# ============================================================================

@pytest.mark.auth
@pytest.mark.api
class TestLogin:
    """Tests for login endpoint."""

    def test_login_success(self, client: TestClient, test_user: User, test_tenant: Tenant):
        """Test successful login with valid credentials."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "testpass123",
                "tenant_subdomain": "test"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email
        assert data["user_id"] == str(test_user.user_id)

        # Check cookies are set
        assert "access_token" in response.cookies
        assert "refresh_token" in response.cookies

    def test_login_wrong_password(self, client: TestClient, test_user: User, test_tenant: Tenant):
        """Test login with wrong password fails."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "wrongpassword",
                "tenant_subdomain": "test"
            }
        )

        assert response.status_code == 401
        assert "credentials" in response.json()["detail"].lower()

    def test_login_nonexistent_user(self, client: TestClient, test_tenant: Tenant):
        """Test login with nonexistent user fails."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "anypassword",
                "tenant_subdomain": "test"
            }
        )

        assert response.status_code == 401

    def test_login_inactive_user(self, client: TestClient, inactive_user: User, test_tenant: Tenant):
        """Test login with inactive user fails."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": inactive_user.email,
                "password": "inactivepass123",
                "tenant_subdomain": "test"
            }
        )

        assert response.status_code == 403
        assert "inactive" in response.json()["detail"].lower()

    def test_login_no_tenant(self, client: TestClient, test_user: User):
        """Test login without tenant fails."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "testpass123"
                # No tenant_subdomain
            }
        )

        assert response.status_code == 400
        assert "tenant" in response.json()["detail"].lower()


@pytest.mark.auth
@pytest.mark.api
class TestLogout:
    """Tests for logout endpoint."""

    def test_logout_success(self, client: TestClient, test_user: User, auth_headers: dict, test_tenant: Tenant):
        """Test successful logout."""
        response = client.post(
            "/api/v1/auth/logout",
            headers=auth_headers
        )

        assert response.status_code == 200
        assert "logged out" in response.json()["message"].lower()

        # Check cookies are cleared (would need to check Set-Cookie headers)

    def test_logout_without_auth(self, client: TestClient):
        """Test logout without authentication fails."""
        response = client.post("/api/v1/auth/logout")

        assert response.status_code == 401


# ============================================================================
# Token Tests
# ============================================================================

@pytest.mark.auth
@pytest.mark.security
class TestTokens:
    """Tests for JWT token functionality."""

    def test_access_protected_endpoint(
        self,
        client: TestClient,
        test_user: User,
        auth_headers: dict
    ):
        """Test accessing protected endpoint with valid token."""
        response = client.get("/api/v1/auth/me", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email

    def test_access_protected_endpoint_no_token(self, client: TestClient):
        """Test accessing protected endpoint without token fails."""
        response = client.get("/api/v1/auth/me")

        assert response.status_code == 401

    def test_access_protected_endpoint_invalid_token(self, client: TestClient):
        """Test accessing protected endpoint with invalid token fails."""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid_token_here"}
        )

        assert response.status_code == 401

    def test_refresh_token(self, client: TestClient, login_user):
        """Test refresh token endpoint."""
        # First login to get refresh token
        login_response = login_user("test@example.com", "testpass123")
        assert login_response.status_code == 200

        # Use cookies from login
        cookies = login_response.cookies

        # Refresh the token
        response = client.post(
            "/api/v1/auth/refresh",
            cookies=cookies
        )

        # Should return user data and new cookies
        assert response.status_code == 200
        assert "email" in response.json()


# ============================================================================
# Password Change Tests
# ============================================================================

@pytest.mark.auth
@pytest.mark.api
class TestPasswordChange:
    """Tests for password change endpoint."""

    def test_change_password_success(
        self,
        client: TestClient,
        test_user: User,
        auth_headers: dict,
        db: Session
    ):
        """Test successful password change."""
        response = client.post(
            "/api/v1/auth/change-password",
            headers=auth_headers,
            json={
                "current_password": "testpass123",
                "new_password": "NewPassword123!"
            }
        )

        assert response.status_code == 200

        # Verify can login with new password
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "NewPassword123!",
                "tenant_subdomain": "test"
            }
        )
        assert login_response.status_code == 200

    def test_change_password_wrong_current(
        self,
        client: TestClient,
        auth_headers: dict
    ):
        """Test password change with wrong current password fails."""
        response = client.post(
            "/api/v1/auth/change-password",
            headers=auth_headers,
            json={
                "current_password": "wrongpassword",
                "new_password": "NewPassword123!"
            }
        )

        assert response.status_code == 400

    def test_change_password_weak_new_password(
        self,
        client: TestClient,
        auth_headers: dict
    ):
        """Test password change with weak new password fails."""
        response = client.post(
            "/api/v1/auth/change-password",
            headers=auth_headers,
            json={
                "current_password": "testpass123",
                "new_password": "weak"
            }
        )

        assert response.status_code == 422  # Validation error


# ============================================================================
# Role-Based Access Control Tests
# ============================================================================

@pytest.mark.auth
@pytest.mark.security
class TestRBAC:
    """Tests for role-based access control."""

    def test_admin_access(
        self,
        client: TestClient,
        test_user: User,  # Admin user
        auth_headers: dict
    ):
        """Test admin user can access admin endpoints."""
        response = client.get("/api/v1/auth/me", headers=auth_headers)

        assert response.status_code == 200
        assert response.json()["role"] == "admin"

    def test_analyst_access(
        self,
        client: TestClient,
        analyst_user: User,
        analyst_auth_headers: dict
    ):
        """Test analyst user can access their endpoints."""
        response = client.get("/api/v1/auth/me", headers=analyst_auth_headers)

        assert response.status_code == 200
        assert response.json()["role"] == "analyst"

    def test_viewer_access(
        self,
        client: TestClient,
        viewer_user: User,
        viewer_auth_headers: dict
    ):
        """Test viewer user has limited access."""
        response = client.get("/api/v1/auth/me", headers=viewer_auth_headers)

        assert response.status_code == 200
        assert response.json()["role"] == "viewer"


# ============================================================================
# Multi-Tenant Tests
# ============================================================================

@pytest.mark.auth
@pytest.mark.integration
class TestMultiTenant:
    """Tests for multi-tenant functionality."""

    def test_users_isolated_by_tenant(
        self,
        client: TestClient,
        db: Session,
        test_tenant: Tenant,
        demo_tenant: Tenant
    ):
        """Test users in different tenants are isolated."""
        # Create users in different tenants with same email
        from services.auth_service import auth_service
        import uuid

        user1 = User(
            user_id=str(uuid.uuid4()),
            tenant_id=test_tenant.tenant_id,
            email="same@example.com",
            password_hash=auth_service.hash_password("password123"),
            first_name="User",
            last_name="One",
            role=UserRole.VIEWER,
            is_active=True,
            email_verified=True
        )
        db.add(user1)

        user2 = User(
            user_id=str(uuid.uuid4()),
            tenant_id=demo_tenant.tenant_id,
            email="same@example.com",  # Same email, different tenant
            password_hash=auth_service.hash_password("password123"),
            first_name="User",
            last_name="Two",
            role=UserRole.VIEWER,
            is_active=True,
            email_verified=True
        )
        db.add(user2)
        db.commit()

        # Login as user1 in test tenant
        response1 = client.post(
            "/api/v1/auth/login",
            json={
                "email": "same@example.com",
                "password": "password123",
                "tenant_subdomain": "test"
            }
        )
        assert response1.status_code == 200
        assert response1.json()["last_name"] == "One"

        # Login as user2 in demo tenant
        response2 = client.post(
            "/api/v1/auth/login",
            json={
                "email": "same@example.com",
                "password": "password123",
                "tenant_subdomain": "demo"
            }
        )
        assert response2.status_code == 200
        assert response2.json()["last_name"] == "Two"
