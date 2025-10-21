# Phase 1: Foundation & Security - Task List

**Timeline:** 1-2 weeks
**Goal:** Secure and stable foundation for development
**Priority:** Critical - Must complete before Phase 2

---

## Relevant Files

### Migrations & Database
- `backend/alembic/versions/YYYYMMDD_HHMM_initial_schema.py` - Initial database migration from models
- `backend/alembic/versions/YYYYMMDD_HHMM_convert_booleans.py` - Convert string booleans to Boolean type
- `backend/alembic/versions/YYYYMMDD_HHMM_unique_constraints.py` - Add unique constraint on user email per tenant
- `backend/models/user.py` - Update boolean field types
- `backend/models/audit_log.py` - Update boolean field types

### Security
- `docker-compose.yml` - Remove weak SECRET_KEY default
- `backend/config.py` - Add SECRET_KEY validation
- `backend/middleware/rate_limit.py` - Rate limiting middleware using slowapi
- `backend/api/auth.py` - Apply rate limits, implement JWT cookie-based auth
- `backend/dependencies/auth.py` - Update token verification for cookies
- `backend/services/auth_service.py` - Add refresh token generation
- `frontend/lib/contexts/AuthContext.tsx` - Update to use httpOnly cookies
- `.env.example` - Document required security settings

### Testing
- `backend/pytest.ini` - pytest configuration
- `backend/.coveragerc` - Coverage reporting configuration
- `backend/tests/conftest.py` - Test fixtures and database setup
- `backend/tests/test_models.py` - Model tests
- `backend/tests/test_rate_limiting.py` - Rate limiting tests
- `backend/tests/test_token_refresh.py` - Token refresh tests
- `backend/requirements.txt` - Add testing dependencies

### CI/CD
- `.github/workflows/backend-tests.yml` - Backend test automation
- `.github/workflows/frontend-tests.yml` - Frontend test automation
- `.github/workflows/security-scan.yml` - Security vulnerability scanning
- `.pre-commit-config.yaml` - Pre-commit hooks configuration

### Scripts & Documentation
- `scripts/generate-secrets.sh` - Generate secure random secrets
- `scripts/run-tests.sh` - Run test suite with coverage
- `scripts/test-watch.sh` - Watch mode for tests
- `scripts/setup-pre-commit.sh` - Install pre-commit hooks
- `README.md` - Update with migration and testing instructions

### Notes
- All migrations must be tested with both upgrade and downgrade
- Run `alembic upgrade head` to apply all migrations
- Run `pytest --cov=.` to check test coverage
- Target: >40% test coverage for Phase 1
- All security changes require verification before proceeding

---

## Tasks

### Database & Schema

- [ ] 1.0 Set up database migrations infrastructure
  - [ ] 1.1 Generate initial Alembic migration from existing models: `alembic revision --autogenerate -m "Initial database schema"`
  - [ ] 1.2 Review generated migration file to verify all tables, foreign keys, indexes, and enums are correct
  - [ ] 1.3 Test migration on fresh database: `docker compose down -v && docker compose up -d postgres && sleep 10 && docker compose exec backend alembic upgrade head`
  - [ ] 1.4 Verify all tables created: `docker compose exec postgres psql -U nexus_admin -d nexus_analyzer -c "\dt"`
  - [ ] 1.5 Test migration rollback: `alembic downgrade -1` then `alembic upgrade head`
  - [ ] 1.6 Update README.md with migration commands and workflow
  - [ ] 1.7 Commit migration file to repository

- [ ] 2.0 Fix string boolean fields to use proper Boolean type
  - [ ] 2.1 Create migration: `alembic revision -m "Convert string booleans to Boolean type"`
  - [ ] 2.2 Write upgrade logic to convert "true"/"false" strings to boolean values in users table (is_active, email_verified)
  - [ ] 2.3 Write upgrade logic to convert success field in audit_log table
  - [ ] 2.4 Write downgrade logic to convert back to strings if needed
  - [ ] 2.5 Update `backend/models/user.py` - change is_active and email_verified from String(10) to Boolean
  - [ ] 2.6 Update `backend/models/audit_log.py` - change success from String(10) to Boolean
  - [ ] 2.7 Find and update all code references: `grep -r "is_active.*=.*['\"]true['\"]" backend/` and replace with boolean True
  - [ ] 2.8 Update comparison logic: change `if user.is_active == "true":` to `if user.is_active:`
  - [ ] 2.9 Update `backend/api/auth.py` with boolean values
  - [ ] 2.10 Update `backend/seeds/fix_demo_user.py` with boolean values
  - [ ] 2.11 Update all test files with boolean values
  - [ ] 2.12 Apply migration and test: Demo user should still login successfully

- [ ] 3.0 Add unique constraint on user email per tenant
  - [ ] 3.1 Create migration: `alembic revision -m "Add unique constraint on user email per tenant"`
  - [ ] 3.2 Write migration to remove any existing duplicate emails (safety check)
  - [ ] 3.3 Add unique constraint in migration: `op.create_unique_constraint('uq_user_email_tenant', 'users', ['email', 'tenant_id'])`
  - [ ] 3.4 Update `backend/models/user.py` to add `UniqueConstraint('email', 'tenant_id', name='uq_user_email_tenant')` in `__table_args__`
  - [ ] 3.5 Add test to verify duplicate emails in same tenant are rejected
  - [ ] 3.6 Add test to verify same email in different tenants is allowed
  - [ ] 3.7 Apply migration and verify registration endpoint returns proper error for duplicates

### Security Hardening

- [ ] 4.0 Secure SECRET_KEY configuration
  - [ ] 4.1 Update `docker-compose.yml` - change SECRET_KEY from `${SECRET_KEY:-your-secret-key-change-in-production}` to `${SECRET_KEY:?SECRET_KEY environment variable is required}` to make it required
  - [ ] 4.2 Add validation in `backend/config.py` - create @field_validator for SECRET_KEY checking minimum 32 characters
  - [ ] 4.3 Add check in validator to reject common weak values like "changeme", "your-secret-key-change-in-production"
  - [ ] 4.4 Create `scripts/generate-secrets.sh` script that uses `openssl rand -hex 32` to generate strong secrets
  - [ ] 4.5 Update `.env.example` with instruction to generate secret: `openssl rand -hex 32`
  - [ ] 4.6 Update README.md with secret generation instructions
  - [ ] 4.7 Test that backend refuses to start without valid SECRET_KEY

- [ ] 5.0 Implement rate limiting on authentication endpoints
  - [ ] 5.1 Add to `backend/requirements.txt`: slowapi==0.1.9
  - [ ] 5.2 Create `backend/middleware/rate_limit.py` with Limiter configured to use Redis storage
  - [ ] 5.3 Create rate_limit_exceeded_handler function returning 429 status with Retry-After header
  - [ ] 5.4 Update `backend/main.py` to add limiter to app.state and register exception handler
  - [ ] 5.5 Update login endpoint in `backend/api/auth.py` to add `@limiter.limit("5/minute")` decorator
  - [ ] 5.6 Update register endpoint to add `@limiter.limit("3/hour")` decorator
  - [ ] 5.7 Add Request parameter to login and register functions (required by limiter)
  - [ ] 5.8 Create `backend/tests/test_rate_limiting.py` to verify 6th login attempt returns 429
  - [ ] 5.9 Test rate limiting works and returns proper Retry-After header
  - [ ] 5.10 Verify rate limiting persists across container restarts (uses Redis)

- [ ] 6.0 Improve JWT token security with httpOnly cookies
  - [ ] 6.1 Update login endpoint in `backend/api/auth.py` to set access_token as httpOnly cookie instead of returning in response body
  - [ ] 6.2 Update login endpoint to set refresh_token as httpOnly cookie with 7-day expiry
  - [ ] 6.3 Update login endpoint to return user info instead of token in response body
  - [ ] 6.4 Create refresh token endpoint at POST /api/v1/auth/refresh that reads refresh_token from cookie
  - [ ] 6.5 Implement refresh token verification and revocation check (check Redis for revoked tokens)
  - [ ] 6.6 Generate new access_token in refresh endpoint and set as httpOnly cookie
  - [ ] 6.7 Update logout endpoint to revoke both access and refresh tokens (add to Redis blacklist with expiry)
  - [ ] 6.8 Update logout endpoint to clear both cookies from response
  - [ ] 6.9 Update `backend/dependencies/auth.py` get_current_user to read token from cookie instead of Authorization header
  - [ ] 6.10 Add revocation check in get_current_user (check Redis blacklist)
  - [ ] 6.11 Update `frontend/lib/contexts/AuthContext.tsx` login function to use `credentials: 'include'` for cookies
  - [ ] 6.12 Remove localStorage.setItem('access_token') from frontend - tokens now in cookies
  - [ ] 6.13 Update frontend refreshAuth function to try refresh endpoint if auth/me returns 401
  - [ ] 6.14 Update frontend logout to call backend logout endpoint with credentials: 'include'
  - [ ] 6.15 Update `frontend/lib/api.ts` to include `credentials: 'include'` in all fetch calls
  - [ ] 6.16 Create `backend/tests/test_token_refresh.py` to test refresh flow
  - [ ] 6.17 Test complete flow: login → get user → refresh token → logout → verify revoked

### Testing Infrastructure

- [ ] 7.0 Set up testing infrastructure with pytest and coverage
  - [ ] 7.1 Add to `backend/requirements.txt`: pytest==7.4.3, pytest-asyncio==0.21.1, pytest-cov==4.1.0, pytest-env==1.1.1, httpx==0.25.2, faker==20.1.0
  - [ ] 7.2 Create `backend/pytest.ini` with testpaths, coverage settings, and test environment variables
  - [ ] 7.3 Set coverage fail threshold to 40% in pytest.ini
  - [ ] 7.4 Create `backend/.coveragerc` to configure coverage reporting and exclude patterns
  - [ ] 7.5 Update `backend/tests/conftest.py` to create test database fixture using SQLite
  - [ ] 7.6 Add test_tenant fixture to conftest.py for creating test tenant
  - [ ] 7.7 Add test_user fixture to conftest.py for creating authenticated test user
  - [ ] 7.8 Add auth_headers fixture that logs in and returns Authorization header with JWT
  - [ ] 7.9 Create `backend/tests/test_models.py` with tests for user creation and tenant relationships
  - [ ] 7.10 Create `scripts/run-tests.sh` to run pytest with coverage and generate HTML report
  - [ ] 7.11 Create `scripts/test-watch.sh` for running pytest in watch mode during development
  - [ ] 7.12 Run tests and verify >40% coverage: `pytest --cov=. --cov-report=term-missing`
  - [ ] 7.13 Fix any failing tests
  - [ ] 7.14 Update README.md with testing instructions

### CI/CD Pipeline

- [ ] 8.0 Set up GitHub Actions CI/CD pipeline
  - [ ] 8.1 Create `.github/workflows/backend-tests.yml` to run tests on every push to main, develop, and claude/** branches
  - [ ] 8.2 Configure PostgreSQL and Redis services in GitHub Actions workflow
  - [ ] 8.3 Add step to cache pip dependencies for faster builds
  - [ ] 8.4 Add step to run database migrations before tests
  - [ ] 8.5 Add step to run pytest with coverage and generate XML report
  - [ ] 8.6 Add step to upload coverage to Codecov
  - [ ] 8.7 Create `.github/workflows/frontend-tests.yml` for frontend linting and build
  - [ ] 8.8 Add npm caching to frontend workflow
  - [ ] 8.9 Add linting step: `npm run lint`
  - [ ] 8.10 Add build step: `npm run build`
  - [ ] 8.11 Create `.github/workflows/security-scan.yml` with Trivy vulnerability scanner
  - [ ] 8.12 Schedule security scan to run weekly on Sundays
  - [ ] 8.13 Configure security scan to upload results to GitHub Security tab
  - [ ] 8.14 Create `.pre-commit-config.yaml` with hooks for: trailing-whitespace, check-yaml, check-json, black formatter, flake8 linter, mypy type checker
  - [ ] 8.15 Create `scripts/setup-pre-commit.sh` to install pre-commit hooks
  - [ ] 8.16 Run setup script and verify pre-commit hooks work: `pre-commit run --all-files`
  - [ ] 8.17 Update README.md with CI/CD information and pre-commit setup instructions

---

## Phase 1 Completion Checklist

Before moving to Phase 2, verify all of the following:

### Migrations ✓
- [ ] Initial migration exists and applies cleanly
- [ ] Boolean conversion migration works
- [ ] Unique constraint migration applied
- [ ] Can upgrade/downgrade all migrations
- [ ] Migration workflow documented in README

### Security ✓
- [ ] SECRET_KEY validation enforced (32+ chars required)
- [ ] Rate limiting active (5/min login, 3/hr registration)
- [ ] JWT tokens in httpOnly cookies (not localStorage)
- [ ] Refresh token endpoint working
- [ ] Token revocation on logout
- [ ] No critical security vulnerabilities in scan

### Database ✓
- [ ] All boolean fields use Boolean type (not strings)
- [ ] Unique constraint prevents duplicate emails per tenant
- [ ] Foreign keys and indexes working
- [ ] Demo user login still works

### Testing ✓
- [ ] Test coverage >40%
- [ ] All tests passing
- [ ] Test fixtures available (tenant, user, auth)
- [ ] Coverage report generates

### CI/CD ✓
- [ ] GitHub Actions running on every push
- [ ] Backend tests pass in CI
- [ ] Frontend build succeeds in CI
- [ ] Security scanning enabled
- [ ] Pre-commit hooks installed

### Documentation ✓
- [ ] README updated with setup instructions
- [ ] Migration commands documented
- [ ] Testing instructions clear
- [ ] Secret generation documented

---

## Time Estimates

| Task | Estimated Time |
|------|----------------|
| 1.0 Database migrations | 4-6 hours |
| 2.0 Fix boolean fields | 3-4 hours |
| 3.0 Unique constraints | 2-3 hours |
| 4.0 Secure SECRET_KEY | 1-2 hours |
| 5.0 Rate limiting | 3-4 hours |
| 6.0 JWT security | 4-5 hours |
| 7.0 Testing infrastructure | 4-5 hours |
| 8.0 CI/CD pipeline | 3-4 hours |
| **Total** | **24-33 hours (1-2 weeks)** |

---

## Execution Order

**Day 1:** Tasks 1.0-2.0 (Migrations foundation)
**Day 2:** Tasks 3.0-5.0 (Constraints + Security basics)
**Day 3:** Task 6.0 (JWT improvements)
**Day 4:** Task 7.0 (Testing)
**Day 5:** Task 8.0 + Documentation + Verification

---

## Common Issues & Solutions

**Migration fails "relation already exists"**
```bash
docker compose down -v
docker compose up -d postgres
docker compose exec backend alembic upgrade head
```

**Tests fail "SECRET_KEY too short"**
```bash
export SECRET_KEY="test-secret-key-minimum-32-characters-long"
```

**Rate limiting not working**
```bash
docker compose logs redis
docker compose exec backend python -c "import redis; r=redis.from_url('redis://redis:6379/1'); print(r.ping())"
```

**Pre-commit hooks failing**
```bash
pre-commit run --all-files
# Fix reported issues, then retry
```

---

## Next Phase

After completing Phase 1, move to **Phase 2: Core Feature Completion** where you'll build:
- CSV upload and validation
- Nexus determination engine
- Tax liability calculations
- Report generation
- Dashboard UI

Phase 1 provides the secure, tested foundation needed to build features confidently.
