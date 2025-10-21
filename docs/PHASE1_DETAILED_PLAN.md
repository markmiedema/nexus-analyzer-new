# Phase 1: Foundation & Security - Detailed Implementation Plan

**Timeline:** 1-2 weeks
**Goal:** Make the application secure and stable for continued development
**Status:** Ready to start

---

## Overview

Phase 1 focuses on fixing critical infrastructure and security issues before building core features. Think of this as "shoring up the foundation before building the house."

### Why Phase 1 First?
- Can't deploy without migrations
- Security vulnerabilities put user data at risk
- Tests prevent regression as we build features
- CI/CD catches issues early

### Success Criteria
- ✅ Database migrations working and applied
- ✅ All Priority 1 security issues resolved
- ✅ Test coverage >40% on critical paths
- ✅ CI/CD pipeline running on every commit
- ✅ No critical vulnerabilities in security scan

---

## Task Breakdown

### Task 1: Database Migrations Setup ⏱️ 4-6 hours

**Priority:** 🔴 Critical (blocking)
**Dependencies:** None

#### Problem
The `backend/alembic/versions/` folder is empty. Without migrations:
- Can't track schema changes
- Can't deploy to production safely
- Team members can't sync database schemas
- Rollbacks are impossible

#### What Needs to Happen

**Step 1.1: Generate Initial Migration**
```bash
cd backend
alembic revision --autogenerate -m "Initial database schema"
```

**Files Created:**
- `backend/alembic/versions/YYYYMMDD_HHMM_initial_database_schema.py`

**Step 1.2: Review Generated Migration**
Check the migration file for:
- All tables are included
- Foreign keys are correct
- Indexes are created
- Enums are properly defined

**Step 1.3: Test Migration Locally**
```bash
# On a fresh database
docker compose down -v
docker compose up -d postgres
sleep 10
docker compose exec backend alembic upgrade head
```

**Step 1.4: Verify Schema**
```bash
docker compose exec postgres psql -U nexus_admin -d nexus_analyzer -c "\dt"
# Should list all tables: users, tenants, analyses, transactions, etc.
```

**Step 1.5: Test Downgrade**
```bash
docker compose exec backend alembic downgrade -1
docker compose exec backend alembic upgrade head
```

#### Acceptance Criteria
- [ ] Migration file generated and committed
- [ ] `alembic upgrade head` succeeds on fresh database
- [ ] All models have corresponding tables
- [ ] Foreign keys and indexes created
- [ ] `alembic downgrade -1` works without errors
- [ ] Documentation updated with migration commands

#### Files to Modify
- Create: `backend/alembic/versions/YYYYMMDD_initial_database_schema.py`
- Update: `README.md` (add migration instructions)

#### Testing
```bash
# Test script
./scripts/test_migrations.sh
```

#### Time Estimate: 4-6 hours

---

### Task 2: Fix String Boolean Fields ⏱️ 3-4 hours

**Priority:** 🔴 Critical
**Dependencies:** Task 1 (migrations must work first)

#### Problem
Models use `is_active = Column(String(10), default="true")` instead of proper booleans.

**Issues:**
- Type confusion ("true" vs "True" vs "1")
- Wastes storage space
- SQLAlchemy filtering issues
- Difficult to query

**Files Affected:**
- `backend/models/user.py` - Lines 59, 60
- `backend/models/audit_log.py` - Line 55

#### What Needs to Happen

**Step 2.1: Create Migration**
```bash
alembic revision -m "Convert string booleans to proper boolean type"
```

**Step 2.2: Write Migration Logic**
```python
# In the generated migration file

def upgrade():
    # Convert user table
    op.execute("""
        UPDATE users
        SET is_active = CASE
            WHEN is_active = 'true' THEN 't'
            WHEN is_active = 'false' THEN 'f'
            ELSE 'f'
        END::boolean
    """)

    op.alter_column('users', 'is_active',
                    type_=sa.Boolean(),
                    postgresql_using='is_active::boolean')

    # Repeat for email_verified
    op.execute("""
        UPDATE users
        SET email_verified = CASE
            WHEN email_verified = 'true' THEN 't'
            WHEN email_verified = 'false' THEN 'f'
            ELSE 'f'
        END::boolean
    """)

    op.alter_column('users', 'email_verified',
                    type_=sa.Boolean(),
                    postgresql_using='email_verified::boolean')

    # Convert audit_log table
    op.execute("""
        UPDATE audit_log
        SET success = CASE
            WHEN success = 'true' THEN 't'
            WHEN success = 'false' THEN 'f'
            ELSE 'f'
        END::boolean
    """)

    op.alter_column('audit_log', 'success',
                    type_=sa.Boolean(),
                    postgresql_using='success::boolean')

def downgrade():
    # Convert back to strings if needed
    op.alter_column('users', 'is_active', type_=sa.String(10))
    op.alter_column('users', 'email_verified', type_=sa.String(10))
    op.alter_column('audit_log', 'success', type_=sa.String(10))
```

**Step 2.3: Update Models**

**File: `backend/models/user.py`**
```python
# Change from:
is_active = Column(String(10), default="true", nullable=False)
email_verified = Column(String(10), default="false", nullable=False)

# To:
is_active = Column(Boolean, default=True, nullable=False, index=True)
email_verified = Column(Boolean, default=False, nullable=False)
```

**File: `backend/models/audit_log.py`**
```python
# Change from:
success = Column(String(10), default="true", nullable=False)

# To:
success = Column(Boolean, default=True, nullable=False)
```

**Step 2.4: Update All Code References**

Search for and update:
```bash
grep -r "is_active.*=.*['\"]true['\"]" backend/
grep -r "email_verified.*=.*['\"]true['\"]" backend/
grep -r "success.*=.*['\"]true['\"]" backend/
```

**Files likely to need updates:**
- `backend/api/auth.py` (lines 80-81, 183)
- `backend/seeds/*.py`
- `backend/tests/*.py`

**Step 2.5: Update Comparisons**
```python
# Change from:
if user.is_active == "true":

# To:
if user.is_active:
```

**Step 2.6: Test Migration**
```bash
# Apply migration
docker compose exec backend alembic upgrade head

# Test queries still work
docker compose exec backend python -c "
from database import SessionLocal
from models.user import User
db = SessionLocal()
users = db.query(User).filter(User.is_active == True).all()
print(f'Found {len(users)} active users')
"
```

#### Acceptance Criteria
- [ ] Migration runs successfully
- [ ] All boolean fields are actual Boolean type
- [ ] All code references updated
- [ ] Tests pass
- [ ] Demo user still logs in successfully
- [ ] No "true"/"false" strings in codebase

#### Files to Modify
- Create: `backend/alembic/versions/YYYYMMDD_convert_string_booleans.py`
- Update: `backend/models/user.py`
- Update: `backend/models/audit_log.py`
- Update: `backend/api/auth.py`
- Update: `backend/seeds/fix_demo_user.py`
- Update: `backend/tests/*.py`

#### Time Estimate: 3-4 hours

---

### Task 3: Add Unique Constraint on User Email ⏱️ 2-3 hours

**Priority:** 🟡 High
**Dependencies:** Task 1

#### Problem
No database constraint prevents duplicate emails within a tenant. This could lead to:
- Data integrity issues
- Authentication confusion
- Race conditions during registration

#### What Needs to Happen

**Step 3.1: Create Migration**
```bash
alembic revision -m "Add unique constraint on user email per tenant"
```

**Step 3.2: Write Migration**
```python
def upgrade():
    # Remove any duplicate emails first (shouldn't exist but be safe)
    op.execute("""
        DELETE FROM users a USING users b
        WHERE a.user_id < b.user_id
        AND a.email = b.email
        AND a.tenant_id = b.tenant_id
    """)

    # Add unique constraint
    op.create_unique_constraint(
        'uq_user_email_tenant',
        'users',
        ['email', 'tenant_id']
    )

def downgrade():
    op.drop_constraint('uq_user_email_tenant', 'users', type_='unique')
```

**Step 3.3: Update Model**

**File: `backend/models/user.py`**
```python
class User(Base):
    __tablename__ = "users"

    # ... existing columns ...

    __table_args__ = (
        UniqueConstraint('email', 'tenant_id', name='uq_user_email_tenant'),
        Index('ix_users_tenant_email', 'tenant_id', 'email'),
        Index('ix_users_tenant_active', 'tenant_id', 'is_active'),
    )
```

**Step 3.4: Add Test**

**File: `backend/tests/test_auth.py`**
```python
def test_duplicate_email_same_tenant_fails():
    """Test that duplicate emails in same tenant are rejected."""
    # Register first user
    response1 = client.post("/api/v1/auth/register", json={
        "email": "duplicate@test.com",
        "password": "Test1234",
        "first_name": "First",
        "last_name": "User",
        "tenant_subdomain": "test"
    })
    assert response1.status_code == 201

    # Try to register same email in same tenant
    response2 = client.post("/api/v1/auth/register", json={
        "email": "duplicate@test.com",
        "password": "Test1234",
        "first_name": "Second",
        "last_name": "User",
        "tenant_subdomain": "test"
    })
    assert response2.status_code == 400
    assert "already registered" in response2.json()["detail"]

def test_duplicate_email_different_tenant_succeeds():
    """Test that same email in different tenants is allowed."""
    # Register in tenant1
    response1 = client.post("/api/v1/auth/register", json={
        "email": "user@test.com",
        "password": "Test1234",
        "first_name": "User",
        "last_name": "One",
        "tenant_subdomain": "tenant1"
    })
    assert response1.status_code == 201

    # Register same email in tenant2
    response2 = client.post("/api/v1/auth/register", json={
        "email": "user@test.com",
        "password": "Test1234",
        "first_name": "User",
        "last_name": "Two",
        "tenant_subdomain": "tenant2"
    })
    assert response2.status_code == 201
```

#### Acceptance Criteria
- [ ] Unique constraint added to database
- [ ] Cannot create duplicate emails within same tenant
- [ ] Can create same email in different tenants
- [ ] Registration endpoint returns proper error for duplicates
- [ ] Tests pass

#### Files to Modify
- Create: `backend/alembic/versions/YYYYMMDD_unique_user_email.py`
- Update: `backend/models/user.py`
- Update: `backend/tests/test_auth.py`

#### Time Estimate: 2-3 hours

---

### Task 4: Secure SECRET_KEY Configuration ⏱️ 1-2 hours

**Priority:** 🔴 Critical (Security)
**Dependencies:** None

#### Problem
Default SECRET_KEY is weak: `"your-secret-key-change-in-production"`

**Risk:** Anyone can forge JWT tokens if they know the default key.

#### What Needs to Happen

**Step 4.1: Remove Default Fallback**

**File: `docker-compose.yml`**
```yaml
# Change from:
SECRET_KEY: ${SECRET_KEY:-your-secret-key-change-in-production}

# To:
SECRET_KEY: ${SECRET_KEY:?SECRET_KEY environment variable is required}
```

**Step 4.2: Add Validation in Config**

**File: `backend/config.py`**
```python
from pydantic_settings import BaseSettings
from pydantic import field_validator

class Settings(BaseSettings):
    SECRET_KEY: str

    @field_validator('SECRET_KEY')
    @classmethod
    def validate_secret_key(cls, v):
        if len(v) < 32:
            raise ValueError('SECRET_KEY must be at least 32 characters')
        if v in ['your-secret-key-change-in-production', 'changeme', 'secret']:
            raise ValueError('SECRET_KEY cannot be a default/weak value')
        return v

    # ... rest of config ...
```

**Step 4.3: Update .env.example**

**File: `.env.example`**
```bash
# Security (REQUIRED)
# Generate with: openssl rand -hex 32
SECRET_KEY=REPLACE_WITH_LONG_RANDOM_STRING_MIN_32_CHARS
```

**Step 4.4: Add Secret Generation Script**

**File: `scripts/generate-secrets.sh`**
```bash
#!/bin/bash
echo "SECRET_KEY=$(openssl rand -hex 32)"
echo "POSTGRES_PASSWORD=$(openssl rand -hex 16)"
echo "MINIO_ROOT_PASSWORD=$(openssl rand -hex 16)"
```

**Step 4.5: Update Documentation**

**File: `README.md`**
```markdown
## Setup

### 1. Generate Secrets

```bash
chmod +x scripts/generate-secrets.sh
./scripts/generate-secrets.sh
# Copy output to .env file
```

### 2. Create .env file

```bash
cp .env.example .env
# Edit .env and paste generated secrets
```
```

#### Acceptance Criteria
- [ ] Cannot start without valid SECRET_KEY
- [ ] SECRET_KEY must be 32+ characters
- [ ] Default weak keys rejected
- [ ] Script to generate secrets provided
- [ ] Documentation updated

#### Files to Modify
- Update: `docker-compose.yml`
- Update: `backend/config.py`
- Update: `.env.example`
- Create: `scripts/generate-secrets.sh`
- Update: `README.md`

#### Time Estimate: 1-2 hours

---

### Task 5: Implement Rate Limiting ⏱️ 3-4 hours

**Priority:** 🔴 Critical (Security)
**Dependencies:** None

#### Problem
No rate limiting on sensitive endpoints allows:
- Brute force password attacks
- API abuse
- DDoS attacks

#### What Needs to Happen

**Step 5.1: Install Dependencies**

**File: `backend/requirements.txt`**
```txt
slowapi==0.1.9
redis==5.0.0  # Should already be installed
```

**Step 5.2: Create Rate Limiter**

**File: `backend/middleware/rate_limit.py`**
```python
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import redis

# Redis client for distributed rate limiting
redis_client = redis.from_url("redis://redis:6379/1")

# Rate limiter instance
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="redis://redis:6379/1",
    default_limits=["100/minute"]
)

def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """Custom handler for rate limit errors."""
    return Response(
        content=f"Rate limit exceeded: {exc.detail}",
        status_code=429,
        headers={"Retry-After": str(exc.retry_after)}
    )
```

**Step 5.3: Apply to Main App**

**File: `backend/main.py`**
```python
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from middleware.rate_limit import limiter

app = FastAPI(...)

# Add rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ... rest of app ...
```

**Step 5.4: Apply to Auth Endpoints**

**File: `backend/api/auth.py`**
```python
from middleware.rate_limit import limiter
from fastapi import Request

@router.post("/login", response_model=Token)
@limiter.limit("5/minute")  # Max 5 login attempts per minute
async def login(
    request: Request,  # Required for rate limiter
    credentials: UserLogin,
    db: Session = Depends(get_db)
):
    # ... existing code ...

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("3/hour")  # Max 3 registrations per hour per IP
async def register(
    request: Request,  # Required for rate limiter
    user_data: UserRegister,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant)
):
    # ... existing code ...
```

**Step 5.5: Add Tests**

**File: `backend/tests/test_rate_limiting.py`**
```python
def test_login_rate_limit():
    """Test that login endpoint is rate limited."""
    # Make 5 requests (should succeed)
    for i in range(5):
        response = client.post("/api/v1/auth/login", json={
            "email": "test@test.com",
            "password": "wrong"
        })
        assert response.status_code in [401, 429]

    # 6th request should be rate limited
    response = client.post("/api/v1/auth/login", json={
        "email": "test@test.com",
        "password": "wrong"
    })
    assert response.status_code == 429
    assert "Rate limit exceeded" in response.text
```

#### Acceptance Criteria
- [ ] Login limited to 5 attempts per minute
- [ ] Registration limited to 3 per hour
- [ ] Rate limit returns 429 status code
- [ ] Retry-After header included
- [ ] Works with multiple containers (uses Redis)
- [ ] Tests pass

#### Files to Modify
- Update: `backend/requirements.txt`
- Create: `backend/middleware/rate_limit.py`
- Update: `backend/main.py`
- Update: `backend/api/auth.py`
- Create: `backend/tests/test_rate_limiting.py`

#### Time Estimate: 3-4 hours

---

### Task 6: Improve JWT Token Security ⏱️ 4-5 hours

**Priority:** 🟡 High (Security)
**Dependencies:** None (but pairs well with Task 5)

#### Problem
Current implementation has security issues:
- Tokens stored in localStorage (XSS vulnerable)
- No token refresh mechanism
- No token revocation (logout is client-side only)
- No token expiry tracking

#### What Needs to Happen

**Step 6.1: Move Tokens to httpOnly Cookies**

**File: `backend/api/auth.py`**
```python
from fastapi.responses import JSONResponse

@router.post("/login")
async def login(
    credentials: UserLogin,
    request: Request,
    response: Response,  # Add Response parameter
    db: Session = Depends(get_db)
):
    # ... existing validation ...

    # Create tokens
    access_token = auth_service.create_access_token(...)
    refresh_token = auth_service.create_refresh_token(...)

    # Set httpOnly cookies instead of returning in body
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,  # Only send over HTTPS
        samesite="lax",
        max_age=1800  # 30 minutes
    )

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=604800  # 7 days
    )

    # Return user info (no token in body)
    return {
        "user": UserResponse(...),
        "message": "Login successful"
    }
```

**Step 6.2: Add Refresh Token Endpoint**

**File: `backend/api/auth.py`**
```python
@router.post("/refresh")
async def refresh_token(
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """Refresh access token using refresh token from cookie."""
    refresh_token = request.cookies.get("refresh_token")

    if not refresh_token:
        raise HTTPException(
            status_code=401,
            detail="Refresh token missing"
        )

    try:
        # Verify refresh token
        payload = auth_service.verify_token(refresh_token)
        user_id = payload.get("user_id")

        # Check if token is revoked
        if redis_client.get(f"revoked:{refresh_token}"):
            raise HTTPException(status_code=401, detail="Token revoked")

        # Get user
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user or not user.is_active:
            raise HTTPException(status_code=401, detail="User not found")

        # Create new access token
        new_access_token = auth_service.create_access_token(
            user_id=str(user.user_id),
            tenant_id=str(user.tenant_id),
            email=user.email,
            role=user.role.value
        )

        # Set new cookie
        response.set_cookie(
            key="access_token",
            value=new_access_token,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=1800
        )

        return {"message": "Token refreshed"}

    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
```

**Step 6.3: Add Token Revocation on Logout**

**File: `backend/api/auth.py`**
```python
from redis import Redis
from config import settings

redis_client = Redis.from_url(settings.REDIS_URL)

@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Logout and revoke tokens."""

    # Get tokens from cookies
    access_token = request.cookies.get("access_token")
    refresh_token = request.cookies.get("refresh_token")

    # Revoke tokens (add to Redis blacklist)
    if access_token:
        redis_client.setex(
            f"revoked:{access_token}",
            1800,  # Expires when token would expire
            "1"
        )

    if refresh_token:
        redis_client.setex(
            f"revoked:{refresh_token}",
            604800,  # 7 days
            "1"
        )

    # Clear cookies
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")

    # Log logout
    audit_log = AuditLog(...)
    db.add(audit_log)
    db.commit()

    return {"message": "Successfully logged out"}
```

**Step 6.4: Update Token Verification**

**File: `backend/dependencies/auth.py`**
```python
async def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
) -> User:
    """Get current user from JWT token in cookie."""

    # Get token from cookie instead of header
    token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated"
        )

    # Check if token is revoked
    if redis_client.get(f"revoked:{token}"):
        raise HTTPException(
            status_code=401,
            detail="Token has been revoked"
        )

    # ... rest of existing verification ...
```

**Step 6.5: Update Frontend**

**File: `frontend/lib/contexts/AuthContext.tsx`**
```typescript
const login = async (credentials: LoginData) => {
  try {
    const response = await fetch(`${apiUrl}/api/v1/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',  // Important: send cookies
      body: JSON.stringify({
        email: credentials.email,
        password: credentials.password,
        tenant_subdomain: 'demo',
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Login failed');
    }

    // No need to store token - it's in httpOnly cookie
    await refreshAuth();
    router.push('/dashboard');
  } catch (error) {
    console.error('Login error:', error);
    throw error;
  }
};

const refreshAuth = async () => {
  try {
    const response = await fetch(`${apiUrl}/api/v1/auth/me`, {
      credentials: 'include',  // Send cookies
    });

    if (response.ok) {
      const userData = await response.json();
      userData.full_name = `${userData.first_name} ${userData.last_name}`;
      setUser(userData);
    } else if (response.status === 401) {
      // Try to refresh token
      const refreshResponse = await fetch(`${apiUrl}/api/v1/auth/refresh`, {
        method: 'POST',
        credentials: 'include',
      });

      if (refreshResponse.ok) {
        // Try getting user again
        await refreshAuth();
      } else {
        setUser(null);
      }
    }
  } catch (error) {
    console.error('Auth refresh error:', error);
    setUser(null);
  } finally {
    setIsLoading(false);
  }
};

const logout = async () => {
  await fetch(`${apiUrl}/api/v1/auth/logout`, {
    method: 'POST',
    credentials: 'include',
  });
  setUser(null);
  router.push('/login');
};
```

#### Acceptance Criteria
- [ ] Tokens stored in httpOnly cookies
- [ ] Refresh token endpoint working
- [ ] Token revocation on logout
- [ ] Revoked tokens rejected
- [ ] Frontend uses cookies instead of localStorage
- [ ] Tests pass

#### Files to Modify
- Update: `backend/api/auth.py`
- Update: `backend/dependencies/auth.py`
- Update: `backend/services/auth_service.py`
- Update: `frontend/lib/contexts/AuthContext.tsx`
- Update: `frontend/lib/api.ts`
- Create: `backend/tests/test_token_refresh.py`

#### Time Estimate: 4-5 hours

---

### Task 7: Set Up Testing Infrastructure ⏱️ 4-5 hours

**Priority:** 🟡 High
**Dependencies:** Tasks 1-3 (need migrations and models fixed)

#### Problem
- Only 3 test files exist
- No test coverage reporting
- No integration tests
- No test database fixtures

#### What Needs to Happen

**Step 7.1: Add Testing Dependencies**

**File: `backend/requirements.txt`**
```txt
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
pytest-env==1.1.1
httpx==0.25.2  # For async test client
faker==20.1.0  # For generating test data
```

**Step 7.2: Configure pytest**

**File: `backend/pytest.ini`**
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto
addopts =
    --cov=.
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=40
    -v
env =
    DATABASE_URL=sqlite:///./test.db
    REDIS_URL=redis://localhost:6379/15
    SECRET_KEY=test-secret-key-min-32-characters-long
    ENVIRONMENT=testing
```

**Step 7.3: Create Test Fixtures**

**File: `backend/tests/conftest.py`**
```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from database import Base, get_db
from main import app
from models.tenant import Tenant, SubscriptionPlan, TenantStatus
from models.user import User, UserRole
from services.auth_service import AuthService
import uuid

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db():
    """Create test database for each test."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db):
    """Create test client with overridden database."""
    def override_get_db():
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def test_tenant(db):
    """Create a test tenant."""
    tenant = Tenant(
        tenant_id=uuid.uuid4(),
        company_name="Test Company",
        subdomain="test",
        subscription_plan=SubscriptionPlan.FREE,
        status=TenantStatus.TRIAL
    )
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return tenant

@pytest.fixture
def test_user(db, test_tenant):
    """Create a test user."""
    auth_service = AuthService()
    user = User(
        user_id=uuid.uuid4(),
        tenant_id=test_tenant.tenant_id,
        email="test@test.com",
        password_hash=auth_service.hash_password("Test1234"),
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
def auth_headers(client, test_user):
    """Get authentication headers for test user."""
    response = client.post("/api/v1/auth/login", json={
        "email": "test@test.com",
        "password": "Test1234",
        "tenant_subdomain": "test"
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
```

**Step 7.4: Create Model Tests**

**File: `backend/tests/test_models.py`**
```python
def test_create_user(db, test_tenant):
    """Test user creation."""
    user = User(
        user_id=uuid.uuid4(),
        tenant_id=test_tenant.tenant_id,
        email="newuser@test.com",
        password_hash="hashed",
        first_name="New",
        last_name="User",
        role=UserRole.VIEWER,
        is_active=True,
        email_verified=False
    )
    db.add(user)
    db.commit()

    assert user.user_id is not None
    assert user.email == "newuser@test.com"
    assert user.is_active is True

def test_user_tenant_relationship(db, test_tenant, test_user):
    """Test user-tenant relationship."""
    assert test_user.tenant_id == test_tenant.tenant_id
    assert test_user in test_tenant.users
```

**Step 7.5: Add Coverage Configuration**

**File: `backend/.coveragerc`**
```ini
[run]
source = .
omit =
    */tests/*
    */alembic/*
    */venv/*
    */__pycache__/*
    */site-packages/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
    if TYPE_CHECKING:
    @abstractmethod
```

**Step 7.6: Add Test Running Scripts**

**File: `scripts/run-tests.sh`**
```bash
#!/bin/bash
cd backend
pytest -v --cov=. --cov-report=html --cov-report=term-missing
echo "Coverage report generated in backend/htmlcov/index.html"
```

**File: `scripts/test-watch.sh`**
```bash
#!/bin/bash
cd backend
pytest-watch -- -v --cov=. --cov-report=term-missing
```

#### Acceptance Criteria
- [ ] pytest configured with coverage
- [ ] Test fixtures for tenant, user, auth
- [ ] Test coverage >40%
- [ ] Coverage report generates
- [ ] Tests run in CI
- [ ] Test documentation added

#### Files to Modify
- Update: `backend/requirements.txt`
- Create: `backend/pytest.ini`
- Create: `backend/.coveragerc`
- Update: `backend/tests/conftest.py`
- Create: `backend/tests/test_models.py`
- Create: `scripts/run-tests.sh`
- Create: `scripts/test-watch.sh`

#### Time Estimate: 4-5 hours

---

### Task 8: Set Up CI/CD Pipeline ⏱️ 3-4 hours

**Priority:** 🟢 Medium
**Dependencies:** Task 7 (tests must work)

#### Problem
- No automated testing
- No code quality checks
- No security scanning
- Manual deployment

#### What Needs to Happen

**Step 8.1: Create GitHub Actions Workflow**

**File: `.github/workflows/backend-tests.yml`**
```yaml
name: Backend Tests

on:
  push:
    branches: [ main, develop, claude/** ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15-alpine
        env:
          POSTGRES_USER: nexus_admin
          POSTGRES_PASSWORD: test_password
          POSTGRES_DB: nexus_analyzer_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

      redis:
        image: redis:7-alpine
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Cache pip dependencies
      uses: actions/cache@v3
      with:
        path: ~/.cache/pip
        key: ${{ runner.os }}-pip-${{ hashFiles('backend/requirements.txt') }}

    - name: Install dependencies
      run: |
        cd backend
        pip install -r requirements.txt

    - name: Run migrations
      env:
        DATABASE_URL: postgresql://nexus_admin:test_password@localhost:5432/nexus_analyzer_test
        SECRET_KEY: test-secret-key-minimum-32-characters
      run: |
        cd backend
        alembic upgrade head

    - name: Run tests
      env:
        DATABASE_URL: postgresql://nexus_admin:test_password@localhost:5432/nexus_analyzer_test
        REDIS_URL: redis://localhost:6379/0
        SECRET_KEY: test-secret-key-minimum-32-characters
      run: |
        cd backend
        pytest --cov=. --cov-report=xml --cov-report=term-missing

    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./backend/coverage.xml
        fail_ci_if_error: false
```

**Step 8.2: Create Frontend Tests Workflow**

**File: `.github/workflows/frontend-tests.yml`**
```yaml
name: Frontend Tests

on:
  push:
    branches: [ main, develop, claude/** ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '20'
        cache: 'npm'
        cache-dependency-path: frontend/package-lock.json

    - name: Install dependencies
      run: |
        cd frontend
        npm ci

    - name: Run linter
      run: |
        cd frontend
        npm run lint

    - name: Build
      run: |
        cd frontend
        npm run build
```

**Step 8.3: Add Security Scanning**

**File: `.github/workflows/security-scan.yml`**
```yaml
name: Security Scan

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]
  schedule:
    - cron: '0 0 * * 0'  # Weekly on Sunday

jobs:
  security:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Run Trivy vulnerability scanner
      uses: aquasecurity/trivy-action@master
      with:
        scan-type: 'fs'
        scan-ref: '.'
        format: 'sarif'
        output: 'trivy-results.sarif'

    - name: Upload Trivy results to GitHub Security
      uses: github/codeql-action/upload-sarif@v2
      with:
        sarif_file: 'trivy-results.sarif'
```

**Step 8.4: Add Pre-commit Hooks**

**File: `.pre-commit-config.yaml`**
```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-json
      - id: check-merge-conflict

  - repo: https://github.com/psf/black
    rev: 23.12.0
    hooks:
      - id: black
        args: [--line-length=100]
        files: ^backend/

  - repo: https://github.com/pycqa/flake8
    rev: 6.1.0
    hooks:
      - id: flake8
        args: [--max-line-length=100, --extend-ignore=E203]
        files: ^backend/

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.7.1
    hooks:
      - id: mypy
        files: ^backend/
```

**Step 8.5: Install Pre-commit**

**File: `scripts/setup-pre-commit.sh`**
```bash
#!/bin/bash
pip install pre-commit
pre-commit install
echo "Pre-commit hooks installed!"
```

#### Acceptance Criteria
- [ ] CI runs on every push
- [ ] Tests run automatically
- [ ] Coverage reported
- [ ] Security scanning enabled
- [ ] Pre-commit hooks installed
- [ ] Documentation updated

#### Files to Modify
- Create: `.github/workflows/backend-tests.yml`
- Create: `.github/workflows/frontend-tests.yml`
- Create: `.github/workflows/security-scan.yml`
- Create: `.pre-commit-config.yaml`
- Create: `scripts/setup-pre-commit.sh`
- Update: `README.md`

#### Time Estimate: 3-4 hours

---

## Task Execution Order

```
Day 1:
  Morning:   Task 1 (Migrations)
  Afternoon: Task 2 (Boolean fields)

Day 2:
  Morning:   Task 3 (Unique constraints)
  Afternoon: Task 4 (SECRET_KEY) + Task 5 (Rate limiting)

Day 3:
  Full day:  Task 6 (JWT security)

Day 4:
  Full day:  Task 7 (Testing infrastructure)

Day 5:
  Morning:   Task 8 (CI/CD)
  Afternoon: Documentation and cleanup
```

---

## Phase 1 Acceptance Checklist

Before moving to Phase 2, verify:

### Migrations
- [ ] Initial migration generated
- [ ] Boolean conversion migration created
- [ ] Unique constraint migration created
- [ ] All migrations apply cleanly on fresh database
- [ ] Migrations documented in README

### Security
- [ ] SECRET_KEY validation enforced
- [ ] Rate limiting active on auth endpoints
- [ ] JWT tokens in httpOnly cookies
- [ ] Token refresh endpoint working
- [ ] Token revocation on logout
- [ ] No critical security vulnerabilities

### Database
- [ ] All boolean fields use Boolean type
- [ ] Unique constraint on user email per tenant
- [ ] All foreign keys working
- [ ] Indexes created

### Testing
- [ ] Test coverage >40%
- [ ] All existing tests pass
- [ ] Test fixtures available
- [ ] Coverage report generates

### CI/CD
- [ ] GitHub Actions running
- [ ] Tests run on every push
- [ ] Pre-commit hooks installed
- [ ] Security scanning enabled

### Documentation
- [ ] README updated with setup instructions
- [ ] Migration commands documented
- [ ] Security best practices documented
- [ ] Testing instructions added

---

## Common Issues & Solutions

### Issue: Migration fails with "relation already exists"
**Solution:** Drop all tables and run migrations on fresh database
```bash
docker compose down -v
docker compose up -d postgres
docker compose exec backend alembic upgrade head
```

### Issue: Tests fail with "SECRET_KEY too short"
**Solution:** Set valid SECRET_KEY in test environment
```bash
export SECRET_KEY="test-secret-key-minimum-32-characters-long"
```

### Issue: Rate limiting not working
**Solution:** Ensure Redis is running and accessible
```bash
docker compose logs redis
docker compose exec backend python -c "import redis; r = redis.from_url('redis://redis:6379/1'); print(r.ping())"
```

### Issue: Pre-commit hooks failing
**Solution:** Run hooks manually to see errors
```bash
pre-commit run --all-files
```

---

## Next Steps After Phase 1

Once Phase 1 is complete, you'll have:
- Secure, stable foundation
- Working database migrations
- Test infrastructure
- CI/CD pipeline

Then you can confidently move to **Phase 2: Building Core Features** where you'll implement:
- CSV upload and processing
- Nexus determination engine
- Tax liability calculations
- Report generation
- Dashboard UI

---

**Ready to start?** Begin with Task 1 (Database Migrations) - it's the foundation for everything else!
