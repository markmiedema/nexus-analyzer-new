# CI/CD Documentation

Comprehensive continuous integration and deployment pipeline for Nexus Analyzer.

## Table of Contents

- [Overview](#overview)
- [Workflows](#workflows)
- [Setup](#setup)
- [Usage](#usage)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)

## Overview

The CI/CD pipeline automates:

- **Code Quality**: Linting, formatting, and static analysis
- **Security**: Dependency scanning and code security checks
- **Testing**: Unit, integration, and end-to-end tests
- **Build**: Docker image creation and caching
- **Deploy**: Automated deployment to staging and production
- **Monitoring**: Test coverage and performance metrics

### Pipeline Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Push/Pull Request                     │
└─────────────────────┬───────────────────────────────────┘
                      │
         ┌────────────┴────────────┐
         │                         │
    ┌────▼─────┐            ┌─────▼──────┐
    │   Lint   │            │  Security  │
    └────┬─────┘            └─────┬──────┘
         │                         │
         └────────────┬────────────┘
                      │
         ┌────────────┴────────────┐
         │                         │
    ┌────▼─────┐            ┌─────▼──────┐
    │ Backend  │            │  Frontend  │
    │  Tests   │            │   Tests    │
    └────┬─────┘            └─────┬──────┘
         │                         │
         └────────────┬────────────┘
                      │
              ┌───────▼────────┐
              │  Docker Build  │
              └───────┬────────┘
                      │
              ┌───────▼────────┐
              │  Integration   │
              │     Tests      │
              └───────┬────────┘
                      │
              ┌───────▼────────┐
              │    Deploy      │
              │  (if tagged)   │
              └────────────────┘
```

## Workflows

### 1. CI Pipeline (`ci.yml`)

**Triggers:**
- Push to `main`, `develop`, or `claude/**` branches
- Pull requests to `main` or `develop`

**Jobs:**

#### Lint and Format Check
- Runs flake8 for code quality
- Checks Black formatting
- Validates import sorting with isort
- Type checking with mypy (optional)

#### Security Scan
- Dependency vulnerability scanning with Safety
- Code security analysis with Bandit
- Reports vulnerabilities (non-blocking)

#### Backend Tests
- Uses PostgreSQL 15 service
- Runs all tests with pytest
- Generates coverage reports
- Uploads coverage to Codecov
- Artifacts: test results, coverage reports

#### Frontend Tests
- Linting and formatting checks
- Unit tests with Jest/Vitest
- Build verification

#### Docker Build
- Builds backend and frontend images
- Uses layer caching for speed
- Validates Dockerfiles

#### Integration Tests
- Spins up full stack with docker-compose
- Runs end-to-end tests
- Smoke tests for critical paths

### 2. Deployment Pipeline (`deploy.yml`)

**Triggers:**
- Manual workflow dispatch
- Version tags (`v*.*.*`)

**Jobs:**

#### Build and Push
- Builds production Docker images
- Pushes to Docker Hub/registry
- Tags with version and latest

#### Deploy to Staging
- Deploys to staging environment
- Runs smoke tests
- Manual approval required

#### Deploy to Production
- Deploys to production environment
- Runs comprehensive health checks
- Sends deployment notifications

#### Database Migrations
- Runs Alembic migrations
- Backs up database before migration
- Rollback on failure

### 3. Dependency Updates (`dependabot.yml`)

**Automated Updates:**
- Python packages (weekly, Mondays)
- npm packages (weekly, Mondays)
- Docker base images (weekly, Mondays)
- GitHub Actions (weekly, Mondays)

**Features:**
- Automatic PR creation
- Security update prioritization
- Grouped updates by ecosystem

## Setup

### 1. Repository Secrets

Configure the following secrets in GitHub repository settings:

#### Required Secrets

```bash
# Docker Hub (for image storage)
DOCKER_USERNAME=your-docker-username
DOCKER_PASSWORD=your-docker-password

# Database (production)
DATABASE_URL=postgresql://user:pass@host:5432/db

# Application secrets
SECRET_KEY=your-secret-key-here

# Codecov (optional, for coverage reports)
CODECOV_TOKEN=your-codecov-token
```

#### Optional Secrets

```bash
# Deployment
SSH_PRIVATE_KEY=your-ssh-key
DEPLOY_HOST=your-server-ip
DEPLOY_USER=your-deploy-user

# Notifications
SLACK_WEBHOOK=your-slack-webhook-url
```

### 2. Enable GitHub Actions

1. Go to repository **Settings** → **Actions** → **General**
2. Under **Actions permissions**, select "Allow all actions and reusable workflows"
3. Under **Workflow permissions**, select "Read and write permissions"

### 3. Branch Protection

Configure branch protection rules:

#### Main Branch
- Require pull request reviews (1+)
- Require status checks to pass:
  - `lint`
  - `test-backend`
  - `test-frontend`
  - `docker-build`
- Require branches to be up to date
- Include administrators

#### Develop Branch
- Require status checks to pass
- Allow force pushes (for development)

### 4. Environments

Create environments for deployment:

#### Staging Environment
- **URL**: https://staging.nexus-analyzer.example.com
- **Protection**: None (auto-deploy)
- **Secrets**: Staging-specific values

#### Production Environment
- **URL**: https://nexus-analyzer.example.com
- **Protection**: Required reviewers (1+)
- **Secrets**: Production values

## Usage

### Running CI Checks Locally

Before pushing code, run checks locally:

```bash
# Backend linting and formatting
cd backend

# Check code quality
flake8 .

# Check formatting (without modifying)
black --check .

# Auto-format code
black .

# Check import sorting
isort --check-only .

# Fix import sorting
isort .

# Run tests
pytest

# Run tests with coverage
pytest --cov=. --cov-report=html
```

### Triggering Workflows

#### Automatic Triggers

```bash
# CI runs automatically on push
git push origin feature-branch

# CI runs on PR creation
gh pr create
```

#### Manual Deployment

```bash
# Via GitHub CLI
gh workflow run deploy.yml \
  -f environment=staging

gh workflow run deploy.yml \
  -f environment=production

# Via GitHub UI
# Go to Actions → Deploy to Production → Run workflow
```

#### Version Release

```bash
# Create and push a version tag
git tag v1.0.0
git push origin v1.0.0

# This automatically triggers:
# 1. CI pipeline
# 2. Docker build and push
# 3. Production deployment (with approval)
```

### Viewing Results

#### Test Results
- **Location**: Actions → [workflow run] → Summary
- **Artifacts**: Download test results and coverage reports
- **Coverage**: View in Codecov dashboard

#### Logs
```bash
# View workflow runs
gh run list

# View specific run logs
gh run view [run-id] --log

# Watch live logs
gh run watch
```

## Configuration

### Code Quality Tools

#### Flake8 (`.flake8`)
- Line length: 127
- Max complexity: 10
- Excludes: venv, migrations, cache

#### Black (`pyproject.toml`)
- Line length: 127
- Target: Python 3.11
- Compatible with Flake8

#### isort (`pyproject.toml`)
- Profile: black (compatible)
- Line length: 127
- Multi-line: 3

### Test Configuration

#### Pytest (`pytest.ini` or `pyproject.toml`)
- Test path: `tests/`
- Coverage minimum: 70%
- Markers: unit, integration, auth, api, security

#### Coverage
- Source: `.` (all code)
- Omit: tests, migrations, venv
- Formats: HTML, XML, terminal

### Docker Build

#### Layer Caching
- Uses GitHub Actions cache
- Speeds up builds by ~70%
- Automatically managed

#### Multi-stage Builds
- Development dependencies separate
- Smaller production images
- Security scanning in CI

## Troubleshooting

### Common Issues

#### 1. Tests Fail in CI but Pass Locally

**Cause**: Environment differences (database, dependencies, secrets)

**Solution**:
```bash
# Use same Python version as CI
pyenv install 3.11
pyenv local 3.11

# Run tests with PostgreSQL locally
docker-compose up -d db
export DATABASE_URL=postgresql://...
pytest
```

#### 2. Docker Build Fails

**Cause**: Context size, cache issues, or Dockerfile errors

**Solution**:
```bash
# Test build locally
docker build -t test:latest -f backend/Dockerfile backend/

# Check build logs
docker build --progress=plain ...

# Clear cache if needed
docker builder prune
```

#### 3. Lint Failures

**Cause**: Code style violations

**Solution**:
```bash
# Auto-fix most issues
black .
isort .

# Check remaining issues
flake8 .
```

#### 4. Coverage Below Threshold

**Cause**: Test coverage < 70%

**Solution**:
```bash
# Find uncovered code
pytest --cov=. --cov-report=term-missing

# View detailed HTML report
pytest --cov=. --cov-report=html
open htmlcov/index.html
```

#### 5. Deployment Fails

**Cause**: Environment configuration, database migrations, or network issues

**Solution**:
```bash
# Check environment secrets
gh secret list

# Test deployment locally
docker-compose up -d

# Check logs
docker-compose logs backend
```

### Getting Help

**CI/CD Issues**:
- Check workflow logs in GitHub Actions
- Review error messages and stack traces
- Search GitHub Issues for similar problems

**Test Issues**:
- Run tests locally with `-vv` for verbose output
- Check test database configuration
- Verify fixture dependencies

**Deployment Issues**:
- Verify environment secrets are set
- Check server logs
- Test health endpoints

## Best Practices

### 1. Keep Builds Fast
- Use caching effectively
- Run fast tests first
- Parallelize when possible
- Skip slow tests in PR checks

### 2. Write Good Commit Messages
```bash
# Good
feat(auth): add JWT refresh token rotation
fix(api): handle rate limit edge case
docs(ci): update deployment guide

# Bad
fixed stuff
update
wip
```

### 3. Use Feature Branches
```bash
# Create feature branch
git checkout -b feature/user-authentication

# Keep it updated
git fetch origin
git rebase origin/main

# Clean commits before merging
git rebase -i origin/main
```

### 4. Monitor Build Times
- Review workflow duration trends
- Optimize slow jobs
- Use matrix builds for parallel testing

### 5. Security
- Never commit secrets
- Rotate credentials regularly
- Review Dependabot PRs promptly
- Enable security alerts

## Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Pytest Documentation](https://docs.pytest.org/)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [PostgreSQL in CI](https://docs.github.com/en/actions/using-containerized-services/creating-postgresql-service-containers)

---

**Last Updated**: 2025-10-21
**Maintainer**: Development Team
**Questions**: Open an issue or contact the team
