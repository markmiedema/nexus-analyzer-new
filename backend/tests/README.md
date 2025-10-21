# Testing Guide

Comprehensive testing infrastructure for Nexus Analyzer backend.

## Table of Contents

- [Overview](#overview)
- [Running Tests](#running-tests)
- [Test Organization](#test-organization)
- [Fixtures](#fixtures)
- [Writing Tests](#writing-tests)
- [Code Coverage](#code-coverage)
- [Best Practices](#best-practices)

## Overview

We use **pytest** as our testing framework with the following features:

- ✅ Isolated test database (in-memory SQLite)
- ✅ Reusable fixtures for common test scenarios
- ✅ Code coverage reporting
- ✅ Test markers for categorization
- ✅ Parallel test execution support

## Running Tests

### Run All Tests

```bash
# From backend directory
pytest

# Or with more verbosity
pytest -v

# Run specific test file
pytest tests/test_auth_comprehensive.py

# Run specific test class
pytest tests/test_auth_comprehensive.py::TestLogin

# Run specific test function
pytest tests/test_auth_comprehensive.py::TestLogin::test_login_success
```

### Run Tests by Marker

```bash
# Run only unit tests (fast)
pytest -m unit

# Run only integration tests
pytest -m integration

# Run only auth tests
pytest -m auth

# Run only API tests
pytest -m api

# Exclude slow tests
pytest -m "not slow"
```

### Run Tests with Coverage

```bash
# Run with coverage report
pytest --cov=. --cov-report=html

# View coverage report (opens in browser)
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

### Run Tests in Docker

```bash
# From project root
docker compose exec backend pytest

# With coverage
docker compose exec backend pytest --cov=. --cov-report=html

# Copy coverage report to host
docker compose cp backend:/app/htmlcov ./htmlcov
```

## Test Organization

```
tests/
├── conftest.py                    # Shared fixtures and configuration
├── test_auth_comprehensive.py     # Authentication tests
├── test_auth.py                   # Legacy auth tests
├── test_business_profile.py       # Business profile tests
├── test_csv_processor.py          # CSV processing tests
└── README.md                      # This file
```

### Test Markers

Tests are categorized using markers defined in `pytest.ini`:

- `@pytest.mark.unit` - Unit tests (fast, isolated)
- `@pytest.mark.integration` - Integration tests (multiple components)
- `@pytest.mark.e2e` - End-to-end tests (full workflows)
- `@pytest.mark.auth` - Authentication tests
- `@pytest.mark.api` - API endpoint tests
- `@pytest.mark.db` - Database tests
- `@pytest.mark.slow` - Slow running tests
- `@pytest.mark.security` - Security tests

## Fixtures

Common fixtures available in `conftest.py`:

### Database Fixtures

- `db` - Fresh database session for each test
- `client` - TestClient with database override

### Tenant Fixtures

- `test_tenant` - Test company tenant
- `demo_tenant` - Demo company tenant

### User Fixtures

- `test_user` - Admin user
- `analyst_user` - Analyst role user
- `viewer_user` - Viewer role user (read-only)
- `inactive_user` - Inactive user (for testing access control)

### Authentication Fixtures

- `auth_headers` - Headers with valid admin JWT token
- `analyst_auth_headers` - Headers with analyst JWT token
- `viewer_auth_headers` - Headers with viewer JWT token

### Helper Fixtures

- `login_user(email, password, tenant)` - Helper to login via API
- `create_user_via_api(...)` - Helper to register user via API

## Writing Tests

### Example Test Structure

```python
import pytest
from fastapi.testclient import TestClient
from models.user import User

@pytest.mark.auth
@pytest.mark.api
class TestAuthentication:
    """Tests for authentication functionality."""

    def test_login_success(self, client: TestClient, test_user: User, test_tenant):
        """Test successful login."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "testpass123",
                "tenant_subdomain": "test"
            }
        )

        assert response.status_code == 200
        assert response.json()["email"] == test_user.email

    def test_login_wrong_password(self, client: TestClient, test_user: User, test_tenant):
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
```

### Using Fixtures

```python
def test_with_authenticated_user(client: TestClient, auth_headers: dict):
    """Example using auth_headers fixture."""
    response = client.get("/api/v1/auth/me", headers=auth_headers)
    assert response.status_code == 200


def test_with_specific_user(client: TestClient, viewer_user: User, viewer_auth_headers: dict):
    """Example using specific user role."""
    response = client.get("/api/v1/auth/me", headers=viewer_auth_headers)
    assert response.json()["role"] == "viewer"
```

### Testing API Endpoints

```python
def test_create_resource(client: TestClient, auth_headers: dict):
    """Example POST request."""
    response = client.post(
        "/api/v1/resource",
        headers=auth_headers,
        json={"name": "test", "value": 123}
    )

    assert response.status_code == 201
    assert response.json()["name"] == "test"


def test_get_resource(client: TestClient, auth_headers: dict):
    """Example GET request."""
    response = client.get(
        "/api/v1/resource/123",
        headers=auth_headers
    )

    assert response.status_code == 200
```

## Code Coverage

### Coverage Configuration

Coverage settings are in `pytest.ini`:

```ini
[coverage:run]
source = .
omit =
    */tests/*
    */seeds/*
    */scripts/*

[coverage:report]
fail_under = 70  # Minimum 70% coverage required
show_missing = True
```

### Viewing Coverage

```bash
# Generate HTML coverage report
pytest --cov=. --cov-report=html

# View in browser
open htmlcov/index.html

# Terminal report with missing lines
pytest --cov=. --cov-report=term-missing

# XML report (for CI/CD)
pytest --cov=. --cov-report=xml
```

### Coverage Reports

After running tests with coverage, you'll get:

1. **Terminal Report** - Quick summary in console
2. **HTML Report** - Detailed interactive report in `htmlcov/`
3. **XML Report** - Machine-readable report for CI/CD

## Best Practices

### 1. Test Organization

```python
# Group related tests in classes
class TestUserManagement:
    """Tests for user management."""

    def test_create_user(self, ...):
        """Test user creation."""
        pass

    def test_update_user(self, ...):
        """Test user update."""
        pass
```

### 2. Test Naming

- Use descriptive names: `test_login_with_invalid_credentials`
- Follow pattern: `test_<what>_<condition>_<expected_result>`
- Add docstrings explaining what the test does

### 3. Arrange-Act-Assert Pattern

```python
def test_example(self, client, test_user):
    # Arrange - Set up test data
    data = {"email": test_user.email, "password": "test"}

    # Act - Perform the action
    response = client.post("/api/v1/auth/login", json=data)

    # Assert - Verify the result
    assert response.status_code == 200
    assert response.json()["email"] == test_user.email
```

### 4. Use Fixtures

```python
# Bad - duplicated setup
def test_1(self, client):
    user = create_user(...)  # Duplicated
    # test code

def test_2(self, client):
    user = create_user(...)  # Duplicated
    # test code

# Good - use fixture
def test_1(self, client, test_user):  # Reuses fixture
    # test code

def test_2(self, client, test_user):  # Reuses fixture
    # test code
```

### 5. Test Isolation

- Each test should be independent
- Don't rely on test execution order
- Use `scope="function"` for fixtures that need fresh state

### 6. Markers

```python
# Mark slow tests
@pytest.mark.slow
def test_large_data_processing(self, ...):
    pass

# Mark security tests
@pytest.mark.security
def test_sql_injection_prevention(self, ...):
    pass

# Mark integration tests
@pytest.mark.integration
def test_full_workflow(self, ...):
    pass
```

### 7. Assertions

```python
# Good - specific assertions
assert response.status_code == 200
assert "email" in response.json()
assert response.json()["role"] == "admin"

# Bad - too generic
assert response  # What does this test?
```

### 8. Error Testing

```python
# Test expected errors
def test_login_wrong_password(self, client, test_user):
    response = client.post("/api/v1/auth/login", json={
        "email": test_user.email,
        "password": "wrong"
    })

    assert response.status_code == 401
    assert "credentials" in response.json()["detail"].lower()
```

## Continuous Integration

Tests run automatically on:

- Every git push
- Every pull request
- Before deployment

See `.github/workflows/` for CI/CD configuration.

## Troubleshooting

### Common Issues

**Tests fail with database errors:**
```bash
# Make sure database is fresh
docker compose down -v
docker compose up -d
```

**Import errors:**
```bash
# Make sure you're in the backend directory
cd backend
pytest
```

**Coverage not working:**
```bash
# Install coverage plugin
pip install pytest-cov
```

**Slow tests:**
```bash
# Run only fast tests
pytest -m "not slow"

# Run in parallel (requires pytest-xdist)
pytest -n auto
```

## Additional Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [SQLAlchemy Testing](https://docs.sqlalchemy.org/en/20/orm/session_transaction.html)
- [Coverage.py](https://coverage.readthedocs.io/)
