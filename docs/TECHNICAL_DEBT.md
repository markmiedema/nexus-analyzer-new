# Technical Debt Inventory

Last Updated: 2025-10-22
Status: Phase 1 Complete - Addressing Post-Foundation Debt

## Overview

This document tracks technical debt items that should be addressed before moving to Phase 2. Items are prioritized by impact and risk.

## Priority Levels

- 🔴 **Critical** - Blocks production deployment or poses security risk
- 🟡 **High** - Impacts reliability or developer productivity
- 🟢 **Medium** - Nice to have, can be deferred
- ⚪ **Low** - Future enhancement, no immediate impact

---

## 1. CI/CD Configuration Issues 🟡 High

### Problem
CI pipeline has 9 steps marked with `continue-on-error: true`, which allows failing checks to pass silently.

### Impact
- Code quality issues may go unnoticed
- Security vulnerabilities could be missed
- Integration test failures are hidden

### Affected Files
`.github/workflows/ci.yml` lines:
- Line 48: flake8 check
- Line 54: black formatting
- Line 60: isort imports
- Line 88: safety vulnerability check
- Line 95: bandit security check
- Line 182: test result uploads
- Line 229: frontend linting
- Line 235: frontend tests (no tests exist yet)
- Line 384: integration tests

### Recommendation
**Priority 1: Remove continue-on-error from security checks** (lines 88, 95)
**Priority 2: Fix lint/format issues and enforce** (lines 48, 54, 60)
**Priority 3: Add frontend tests or remove the step** (line 235)
**Priority 4: Fix integration tests to pass** (line 384)

### Effort Estimate
2-4 hours

---

## 2. Celery Configuration Warnings 🟡 High

### Problem
Celery worker logs show deprecation warnings:
```
CPendingDeprecationWarning: The broker_connection_retry configuration setting will no longer determine
whether broker connection retries are made during startup in Celery 6.0 and above.
If you wish to retain the existing behavior for retrying connections on startup,
you should set broker_connection_retry_on_startup to True.
```

### Impact
- Code will break in Celery 6.0
- Log noise makes real issues harder to spot

### Affected Files
- `backend/workers/celery_app.py`

### Recommendation
Add configuration:
```python
broker_connection_retry_on_startup = True
```

### Effort Estimate
15 minutes

---

## 3. Missing Frontend Tests 🟡 High

### Problem
Frontend test step reports: "No frontend tests configured yet"

### Impact
- No automated testing for frontend components
- Type safety is enforced but runtime behavior is not tested
- UI regressions could go undetected

### Affected Files
- `frontend/package.json` - test script undefined
- `.github/workflows/ci.yml` line 229-235

### Recommendation
**Option 1**: Add Jest + React Testing Library tests
**Option 2**: Add Playwright E2E tests
**Option 3**: Document as "deferred to Phase 2" and remove CI step

### Effort Estimate
4-8 hours (Option 1 or 2)
15 minutes (Option 3 - documentation only)

---

## 4. Code TODOs 🟢 Medium

### 4.1 Email Sending for Reports
**File**: `backend/api/reports.py:380`
```python
# TODO: Implement email sending
```

**Description**: Report email endpoint exists but doesn't send emails

**Impact**: Feature incomplete, API returns 200 but doesn't fulfill promise

**Recommendation**:
- Document as "Phase 2 feature" in API docs
- Add warning log when endpoint is called
- Or implement basic email sending with templates

**Effort**: 2-4 hours

---

### 4.2 CSV Virus Scanning
**File**: `backend/api/csv_processor.py:105`
```python
# TODO: Add virus scanning placeholder
# For production, integrate with ClamAV or similar
```

**Description**: Uploaded CSV files are not scanned for malware

**Impact**: Security risk - malicious files could be uploaded

**Priority**: 🔴 Critical for production

**Recommendation**:
- Add ClamAV integration for production
- Add file size limits (currently missing)
- Add file type validation beyond extension check

**Effort**: 4-6 hours

---

## 5. Secret Key Warnings 🟢 Medium

### Problem
Backend logs show SECRET_KEY validation warnings in test/dev:
```
WARNING: SECRET_KEY appears to contain weak/example text: 'secret'
WARNING: SECRET_KEY appears to contain weak/example text: 'test'
```

### Impact
- Log noise in CI/CD
- Could accidentally use weak keys in production

### Affected Files
- `backend/config.py` - validation logic
- `.github/workflows/ci.yml` - test environment variables
- `docker-compose.yml` - development environment

### Recommendation
- Suppress warnings when ENVIRONMENT=test or CI=true
- Keep warnings for development and production
- Update CI to use properly formatted test keys

### Effort Estimate
30 minutes

---

## 6. Missing Integration Test Markers 🟢 Medium

### Problem
Integration tests run all tests because pytest markers aren't implemented:
```yaml
# Removed -m integration filter since tests may not have markers yet
```

### Impact
- Integration tests take longer than necessary
- Can't run unit tests separately from integration tests

### Affected Files
- All test files in `backend/tests/`
- `.github/workflows/ci.yml` line 382

### Recommendation
Add pytest markers:
```python
@pytest.mark.integration
@pytest.mark.unit
@pytest.mark.slow
```

### Effort Estimate
1-2 hours

---

## 7. Lint/Format Enforcement ⚪ Low

### Problem
Code formatting and linting are checked but not enforced in CI

### Impact
- Code style inconsistencies
- Import ordering varies

### Affected Files
- `.github/workflows/ci.yml` lines 48, 54, 60
- `.pre-commit-config.yaml` exists but may not be used

### Recommendation
**Option 1**: Run pre-commit hooks in CI and fail on errors
**Option 2**: Fix all existing lint issues first, then remove continue-on-error
**Option 3**: Keep as warnings for now, enforce in Phase 2

### Effort Estimate
2-4 hours (Option 1 or 2)

---

## 8. Documentation Gaps ⚪ Low

### Missing Documentation
- ✅ `.github/README.md` - EXISTS (508 lines)
- ✅ `.github/QUICK_REFERENCE.md` - EXISTS (202 lines)
- ✅ `backend/tests/README.md` - EXISTS (430 lines)
- ✅ `docs/SECURITY.md` - EXISTS (348 lines)
- ❌ `docs/API.md` - API documentation (OpenAPI/Swagger exists via FastAPI)
- ❌ `docs/DEPLOYMENT.md` - Production deployment guide
- ❌ `CONTRIBUTING.md` - Contribution guidelines

### Recommendation
Add missing documentation in Phase 2 or before production

### Effort Estimate
4-6 hours total

---

## Summary of Recommendations

### Must Address Before Phase 2
1. 🔴 **CSV Virus Scanning** - Security critical
2. 🟡 **Celery Deprecation Warning** - 15 min fix
3. 🟡 **Remove continue-on-error from security scans** - 30 min fix

### Should Address Before Phase 2
4. 🟡 **Add Frontend Tests or Document Deferral** - 15 min to 8 hours
5. 🟡 **Fix Integration Tests** - 2-4 hours
6. 🟢 **Secret Key Warning Suppression** - 30 min

### Can Defer to Phase 2
7. 🟢 **Email Sending Implementation** - Feature incomplete
8. 🟢 **Integration Test Markers** - Nice to have
9. ⚪ **Lint/Format Enforcement** - Code quality
10. ⚪ **Additional Documentation** - Can add as needed

---

## Proposed Action Plan

**Session Goal**: Address high-priority items to ensure Phase 2 has a solid foundation

### Quick Wins (Est: 1-2 hours)
1. Fix Celery deprecation warning
2. Remove continue-on-error from security scans
3. Suppress SECRET_KEY warnings in test environments
4. Document frontend tests as "Phase 2" and remove from CI

### Medium Priority (Est: 2-4 hours)
5. Fix integration tests to pass reliably
6. Add file size limits and basic validation to CSV upload

### Can Defer
- Email sending (Phase 2 feature)
- Virus scanning with ClamAV (production requirement)
- pytest markers
- Lint enforcement
- Additional documentation

**Total Estimated Effort for Quick Wins**: 1-2 hours
**Total Estimated Effort for All High Priority**: 4-8 hours

