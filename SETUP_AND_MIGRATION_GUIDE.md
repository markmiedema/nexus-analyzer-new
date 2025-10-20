# Nexus Analyzer - Setup and Migration Guide

## Prerequisites

1. **Docker Desktop** must be installed and running
2. **Git** for version control (optional)

## Step-by-Step Setup

### 1. Start Docker Desktop

Ensure Docker Desktop is running. You can verify with:
```bash
docker --version
docker ps
```

### 2. Navigate to Project Directory

```bash
cd E:\nexus-analyzer
```

### 3. Start Database Services

Start PostgreSQL, Redis, and MinIO services:

```bash
# Start all infrastructure services
docker-compose up -d postgres redis minio

# Check service status (wait until all are healthy)
docker-compose ps

# View logs if needed
docker-compose logs -f postgres
```

**Wait for services to be healthy** (usually 10-30 seconds). PostgreSQL must be fully started before proceeding.

### 4. Generate Alembic Migration

Generate the initial database migration from your SQLAlchemy models:

```bash
# Option 1: Using docker-compose exec (recommended)
docker-compose run --rm backend alembic revision --autogenerate -m "Initial schema with all tables"

# Option 2: Using local Python environment
cd backend
..\venv\Scripts\activate  # Windows
alembic revision --autogenerate -m "Initial schema with all tables"
```

This will create a new migration file in `backend/alembic/versions/`.

### 5. Review the Migration

**IMPORTANT**: Always review auto-generated migrations before applying them!

```bash
# Find the migration file
dir backend\alembic\versions  # Windows
ls backend/alembic/versions   # Linux/Mac

# Open and review the migration file
# Look for the YYYYMMDD_HHMM-<hash>_initial_schema_with_all_tables.py file
```

Check that all 12 tables are included:
- ✓ tenants
- ✓ users
- ✓ analyses
- ✓ business_profiles
- ✓ physical_locations
- ✓ transactions
- ✓ nexus_rules
- ✓ nexus_results
- ✓ liability_estimates
- ✓ state_tax_config
- ✓ reports
- ✓ audit_log

### 6. Run the Migration

Apply the migration to create all database tables:

```bash
# Option 1: Using docker-compose (recommended)
docker-compose exec backend alembic upgrade head

# Option 2: Using local Python environment
cd backend
..\venv\Scripts\activate  # Windows
alembic upgrade head
```

### 7. Verify Database Schema

Connect to PostgreSQL and verify tables were created:

```bash
# Connect to PostgreSQL container
docker-compose exec postgres psql -U nexus_admin -d nexus_analyzer

# Inside PostgreSQL, run:
\dt                          # List all tables
\d tenants                   # Describe tenants table
\d users                     # Describe users table
SELECT version_num FROM alembic_version;  # Check migration version
\q                           # Quit
```

Expected output: You should see all 12 tables listed.

### 8. Start Application Services (Optional)

Once the database is set up, you can start the application:

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000/docs
# MinIO Console: http://localhost:9001
```

## Common Issues and Solutions

### Issue: Docker not responding

**Solution**: Ensure Docker Desktop is running
```bash
# Check Docker status
docker --version
docker ps
```

### Issue: Port already in use

**Solution**: Stop conflicting services or change ports in `.env`
```bash
# Find what's using port 5432
netstat -ano | findstr :5432  # Windows
lsof -i :5432                 # Linux/Mac

# Or change port in .env file
POSTGRES_PORT=5433
```

### Issue: Database connection refused

**Solution**: Wait for PostgreSQL to fully start
```bash
# Check PostgreSQL logs
docker-compose logs postgres

# Wait for this message:
# "database system is ready to accept connections"
```

### Issue: Alembic can't find models

**Solution**: Ensure you're in the backend directory and models are imported
```bash
cd backend
# Check that models/__init__.py imports all models
```

### Issue: Migration has no changes detected

**Solution**:
1. Check that `alembic/env.py` imports models correctly
2. Verify `database.py` has Base defined
3. Ensure DATABASE_URL is set in `.env`

## Rollback Instructions

If you need to rollback a migration:

```bash
# Rollback one migration
docker-compose exec backend alembic downgrade -1

# Rollback to specific revision
docker-compose exec backend alembic downgrade <revision>

# Rollback all migrations (WARNING: destroys all data)
docker-compose exec backend alembic downgrade base
```

## Fresh Start

To completely reset the database:

```bash
# Stop all services
docker-compose down

# Remove volumes (WARNING: deletes all data)
docker-compose down -v

# Start fresh
docker-compose up -d postgres redis minio

# Wait for services to be healthy, then run migrations
docker-compose exec backend alembic upgrade head
```

## Next Steps

After completing the migration:

1. ✅ Section 1.0 - Infrastructure Setup (COMPLETED)
2. ✅ Section 2.0 - Database Schema (COMPLETED)
3. ⏭️ Section 3.0 - Authentication & User Management
4. ⏭️ Section 4.0 - CSV Upload & Processing
5. ⏭️ Section 5.0 - Business Profile Management

## Verification Checklist

- [ ] Docker Desktop is running
- [ ] All services are up and healthy (`docker-compose ps`)
- [ ] PostgreSQL accepts connections
- [ ] Migration file was generated successfully
- [ ] Migration was applied (`alembic upgrade head`)
- [ ] All 12 tables exist in database
- [ ] `alembic_version` table shows current revision

## Support

If you encounter issues:
1. Check the logs: `docker-compose logs <service-name>`
2. Verify `.env` file exists and has correct values
3. Ensure all ports are available (5432, 6379, 9000, 8000, 3000)
4. Try a fresh start (see above)

---

**Last Updated**: October 2025
**Version**: Phase 1 MVP
