# CI/CD Quick Reference

Quick commands and common tasks for the Nexus Analyzer CI/CD pipeline.

## Local Development

### Run All Checks Before Push
```bash
# From backend directory
cd backend

# Format code
black .
isort .

# Lint
flake8 .

# Run tests
pytest -v

# Run tests with coverage
pytest --cov=. --cov-report=html

# Run only fast tests
pytest -m "not slow"
```

### Docker Commands
```bash
# Build and run locally
docker-compose up -d

# Run tests in container
docker-compose exec backend pytest

# View logs
docker-compose logs -f backend

# Rebuild after changes
docker-compose up -d --build

# Clean up
docker-compose down -v
```

## GitHub Actions

### View Workflow Status
```bash
# List recent runs
gh run list

# View specific run
gh run view [run-id]

# Watch live run
gh run watch

# Download artifacts
gh run download [run-id]
```

### Trigger Manual Workflows
```bash
# Deploy to staging
gh workflow run deploy.yml -f environment=staging

# Deploy to production
gh workflow run deploy.yml -f environment=production
```

## Git Workflow

### Feature Development
```bash
# Create feature branch
git checkout -b feature/my-feature

# Make changes and commit
git add .
git commit -m "feat: add new feature"

# Push and create PR
git push -u origin feature/my-feature
gh pr create
```

### Version Release
```bash
# Create and push tag
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0

# This triggers automatic deployment
```

## Common Tasks

### Fix Linting Issues
```bash
# Auto-fix formatting
black .
isort .

# Check remaining issues
flake8 .
```

### Update Dependencies
```bash
# Backend
pip install -r requirements.txt --upgrade

# Frontend
cd frontend
npm update
```

### Check Test Coverage
```bash
# Generate HTML report
pytest --cov=. --cov-report=html

# Open in browser
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

### Database Migrations
```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Environment Variables

### Required for Local Testing
```bash
export DATABASE_URL=postgresql://user:pass@localhost:5432/nexus_db
export SECRET_KEY=your-secret-key-here
export ENVIRONMENT=development
```

### Required GitHub Secrets
- `DOCKER_USERNAME`
- `DOCKER_PASSWORD`
- `DATABASE_URL`
- `SECRET_KEY`
- `CODECOV_TOKEN` (optional)

## Troubleshooting

### CI Failing?
1. Check workflow logs: `gh run view --log`
2. Run tests locally: `pytest -v`
3. Check lint: `flake8 .`
4. Verify Docker build: `docker build -t test .`

### Tests Passing Locally But Failing in CI?
1. Check Python version matches (3.11)
2. Verify DATABASE_URL uses PostgreSQL
3. Check for missing dependencies
4. Review environment variables

### Deployment Failing?
1. Verify secrets are set: `gh secret list`
2. Check environment configuration
3. Review deployment logs
4. Test health endpoints

## Useful Links

- **Actions Dashboard**: `https://github.com/[owner]/[repo]/actions`
- **Security Alerts**: `https://github.com/[owner]/[repo]/security`
- **Dependabot**: `https://github.com/[owner]/[repo]/security/dependabot`
- **Environments**: `https://github.com/[owner]/[repo]/settings/environments`

## CI/CD Pipeline Status

### Jobs Run on Every Push/PR
- ✅ Lint and Format Check (~2 min)
- ✅ Security Scan (~3 min)
- ✅ Backend Tests (~5 min)
- ✅ Frontend Tests (~3 min)
- ✅ Docker Build (~4 min)
- ✅ Integration Tests (~6 min)

**Total Time**: ~15-20 minutes

### Jobs Run on Version Tags
All CI jobs + Deployment (~25-30 minutes)

---

**Need Help?** See [full documentation](.github/README.md) or open an issue.
