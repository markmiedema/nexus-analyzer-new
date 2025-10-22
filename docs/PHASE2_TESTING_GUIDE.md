# Phase 2 Testing Guide

**Date**: 2025-10-22
**Purpose**: Complete end-to-end testing instructions for Phase 2 Core Analysis Features

---

## Overview

Phase 2 is **~95% implemented**. This guide provides step-by-step instructions to:
1. Initialize the database
2. Seed reference data
3. Test the complete analysis workflow
4. Verify all features work correctly
5. Document and fix any bugs

**Estimated Testing Time**: 4-6 hours for comprehensive testing

---

## Prerequisites

### Required Services
- Docker and Docker Compose installed
- All services defined in `docker-compose.yml`:
  - PostgreSQL database
  - Redis (for Celery)
  - MinIO (S3-compatible storage)
  - Backend API
  - Frontend
  - Celery worker

### Test Data
- Sample CSV file with transaction data (see Sample CSV Format below)
- Test user credentials

---

## Step 1: Start All Services

### 1.1 Start Docker Services

```bash
# From project root
docker compose up -d

# Verify all services are running
docker compose ps

# Expected output:
# NAME                  STATUS
# postgres              Up
# redis                 Up
# minio                 Up
# backend               Up
# frontend              Up
# celery-worker         Up
```

### 1.2 Check Service Health

```bash
# Backend health check
curl http://localhost:8000/health
# Expected: {"status": "healthy", "version": "0.1.0"}

# Frontend health check
curl http://localhost:3000
# Expected: HTML response

# MinIO console
open http://localhost:9001
# Credentials from .env: MINIO_ROOT_USER / MINIO_ROOT_PASSWORD
```

---

## Step 2: Initialize Database

### 2.1 Run Migrations

```bash
# Enter backend container
docker compose exec backend bash

# Run Alembic migrations
alembic upgrade head

# Verify tables were created
python -c "
from sqlalchemy import create_engine, inspect
from config import settings

engine = create_engine(settings.DATABASE_URL)
inspector = inspect(engine)
tables = inspector.get_table_names()

print('=== DATABASE TABLES ===')
for table in sorted(tables):
    print(f'  ✓ {table}')

# Expected tables:
# analyses
# audit_log
# business_profiles
# liability_estimates
# nexus_results
# nexus_rules
# physical_locations
# reports
# state_tax_config
# tenants
# transactions
# users
"
```

### 2.2 Seed Reference Data

```bash
# Still in backend container

# Seed nexus rules (47 states)
python seeds/nexus_rules_seed.py

# Seed state tax configuration (50 states + DC)
python seeds/state_tax_config_seed.py

# Verify seed data
python -c "
from sqlalchemy import create_engine, text
from config import settings

engine = create_engine(settings.DATABASE_URL)
with engine.connect() as conn:
    nexus_count = conn.execute(text('SELECT COUNT(*) FROM nexus_rules')).scalar()
    state_count = conn.execute(text('SELECT COUNT(*) FROM state_tax_config')).scalar()

    print(f'Nexus rules: {nexus_count} (expected: 47)')
    print(f'State tax configs: {state_count} (expected: 51)')
"
```

### 2.3 Create Demo User

```bash
# Create a demo user for testing
python seeds/create_demo_user.py

# Verify user was created
python seeds/verify_demo_user.py

# Expected output:
# ✓ Demo user exists
# Email: demo@example.com
# Password: demo123
```

---

## Step 3: End-to-End Workflow Testing

### 3.1 Login to Frontend

1. Open browser: http://localhost:3000
2. Login with demo credentials:
   - Email: `demo@example.com`
   - Password: `demo123`
3. Verify you reach the dashboard

### 3.2 Create New Analysis

**Path**: Dashboard → "New Analysis" button

#### Step 1: Basic Information
- **Client Name**: "Test Company Inc."
- **Period Start**: 2024-01-01
- **Period End**: 2024-12-31
- Click **"Continue"**

**Expected Behavior**:
- Form validation passes
- Analysis record created in database
- Redirect to CSV upload step

**Verification**:
```bash
# Check database
docker compose exec backend python -c "
from database import SessionLocal
from models.analysis import Analysis

db = SessionLocal()
analysis = db.query(Analysis).order_by(Analysis.created_at.desc()).first()
if analysis:
    print(f'✓ Analysis created: {analysis.analysis_id}')
    print(f'  Client: {analysis.client_name}')
    print(f'  Status: {analysis.status}')
else:
    print('✗ No analysis found')
db.close()
"
```

#### Step 2: CSV Upload

1. Click **"Choose File"**
2. Select a CSV file (see Sample CSV Format below)
3. Click **"Continue"**

**Expected Behavior**:
- File uploads successfully
- File stored in MinIO S3 bucket
- Celery task `process_csv_file` triggered
- Status changes to `PROCESSING_CSV`
- Redirect to business profile step

**Verification**:
```bash
# Check Celery worker logs
docker compose logs celery-worker --tail=50

# Expected log entries:
# [INFO] Task workers.tasks.process_csv_file[task-id] received
# [INFO] Processing CSV file for analysis: [analysis-id]
# [INFO] Parsed 100 transactions
# [SUCCESS] Task workers.tasks.process_csv_file[task-id] succeeded

# Check transactions in database
docker compose exec backend python -c "
from database import SessionLocal
from models.transaction import Transaction
from sqlalchemy import func

db = SessionLocal()
count = db.query(func.count(Transaction.transaction_id)).scalar()
print(f'Transactions imported: {count}')
db.close()
"
```

**Troubleshooting CSV Upload**:
- If upload fails with 413: Increase `client_max_body_size` in nginx
- If MinIO connection fails: Check MinIO credentials in `.env`
- If Celery task not triggered: Check Redis connection

#### Step 3: Business Profile

Fill out business information:
- **Legal Business Name**: "Test Company Inc."
- **Business Structure**: "LLC"
- **Has Physical Presence**: Yes/No
- **Has Employees**: Yes/No
- **Has Inventory**: Yes/No
- Add **Physical Locations** if applicable
- **Marketplace Facilitators**: List any (e.g., "Amazon", "eBay")

Click **"Submit"**

**Expected Behavior**:
- Business profile saved
- Celery task `run_nexus_determination` triggered
- Status changes to `PROCESSING_NEXUS`
- Redirect to analysis detail page

**Verification**:
```bash
# Check Celery logs for nexus determination
docker compose logs celery-worker --tail=100 | grep nexus

# Expected:
# [INFO] Task workers.tasks.run_nexus_determination received
# [INFO] Running nexus determination for analysis: [analysis-id]
# [INFO] Checking nexus for 50 states
# [SUCCESS] Task succeeded: Found nexus in 5 states
```

### 3.3 View Results

**Path**: Dashboard → Analyses → [Your Analysis]

#### Verify Analysis Detail Page

**Page Sections**:
1. **Header**: Analysis status, dates, client name
2. **Status Tracker**: Visual progress (pending → processing → completed)
3. **Nexus Results Table**:
   - States with nexus
   - Sales amounts
   - Transaction counts
   - Thresholds
   - Nexus status (Has Nexus, No Nexus, Approaching)
4. **Liability Estimates** (if calculated):
   - Estimated tax liability by state
   - Risk levels
5. **Actions**:
   - Generate Report buttons
   - Download CSV

**Expected Data**:
- All states analyzed (50 rows)
- Correct nexus determination based on:
  - Sales threshold (e.g., $100k, $500k for CA)
  - Transaction threshold (e.g., 200 transactions)
  - Physical presence locations
- Confidence levels (High/Medium/Low)
- Registration deadlines calculated

**Verification Queries**:
```bash
docker compose exec backend python -c "
from database import SessionLocal
from models.nexus_result import NexusResult
from models.analysis import Analysis, AnalysisStatus

db = SessionLocal()

# Get latest analysis
analysis = db.query(Analysis).order_by(Analysis.created_at.desc()).first()

if analysis:
    print(f'Analysis: {analysis.analysis_id}')
    print(f'Status: {analysis.status}')

    # Get nexus results
    results = db.query(NexusResult).filter_by(analysis_id=analysis.analysis_id).all()

    print(f'\nNexus Results: {len(results)} states')

    has_nexus = [r for r in results if r.overall_determination == 'HAS_NEXUS']
    approaching = [r for r in results if r.overall_determination == 'CLOSE_TO_THRESHOLD']

    print(f'  Has Nexus: {len(has_nexus)} states')
    print(f'  Approaching: {len(approaching)} states')

    if has_nexus:
        print('\nStates with Nexus:')
        for r in has_nexus[:5]:
            print(f'  {r.state}: ${r.total_sales:,.2f} sales, {r.total_transactions} txns')

db.close()
"
```

### 3.4 Generate Reports

#### PDF Summary Report

1. Click **"Generate Summary Report"**
2. Wait for generation (5-15 seconds)
3. Click **"Download"** when ready

**Expected Report Contents**:
- Executive summary
- Nexus determination summary
- States requiring registration
- Total liability estimate
- Key recommendations
- Charts/visualizations

**Verification**:
```bash
# Check reports table
docker compose exec backend python -c "
from database import SessionLocal
from models.report import Report

db = SessionLocal()
reports = db.query(Report).order_by(Report.created_at.desc()).limit(5).all()

print('Recent Reports:')
for r in reports:
    print(f'  {r.report_type}: {r.status} - {r.file_path}')

db.close()
"

# Check MinIO for report file
# Login to MinIO console: http://localhost:9001
# Navigate to 'reports' bucket
# Verify PDF file exists
```

#### Excel Detailed Report

1. Click **"Generate Detailed Report"**
2. Wait for generation
3. Download Excel file

**Expected Excel Sheets**:
1. Summary
2. Nexus Results (all states)
3. Liability Estimates
4. Transaction Details (sample)
5. Recommendations

---

## Step 4: Feature-Specific Testing

### 4.1 CSV Validation Testing

**Test Invalid CSVs**:

Create test files with common issues:

**Missing Required Columns**:
```csv
date,amount
2024-01-01,100.00
```
Expected: Error message "Missing required column: state"

**Invalid State Codes**:
```csv
date,state,amount
2024-01-01,XX,100.00
```
Expected: Warning about invalid state code

**Invalid Date Formats**:
```csv
date,state,amount
01-01-2024,CA,100.00
```
Expected: Date parsing or error

**Negative Amounts**:
```csv
date,state,amount
2024-01-01,CA,-100.00
```
Expected: Warning or error

**Test API Endpoint**:
```bash
# Get validation report
curl http://localhost:8000/api/v1/csv/validation-report/{analysis_id}

# Expected response:
{
  "analysis_id": "...",
  "total_rows": 100,
  "valid_rows": 95,
  "invalid_rows": 5,
  "errors": [
    {
      "row": 10,
      "column": "state",
      "error": "Invalid state code: XX"
    }
  ]
}
```

### 4.2 Nexus Engine Testing

**Test Physical Nexus**:

Create analysis with physical locations in CA, NY, TX:
- Expected: Physical nexus in these 3 states
- Economic nexus calculation for remaining states

**Test Economic Nexus Thresholds**:

Upload CSV with specific sales amounts:
- CA: $499,999 sales → "CLOSE_TO_THRESHOLD"
- CA: $500,001 sales → "HAS_NEXUS"
- TX: $100,000 sales → "HAS_NEXUS"

**Test Marketplace Facilitator Logic**:

- Profile with `uses_marketplace_facilitators: true`
- Transactions with `is_marketplace_sale: true`
- Expected: Marketplace sales excluded from nexus calculation (if state has marketplace law)

**Test Transaction Thresholds**:

For states with transaction thresholds (e.g., AR, CT):
- 199 transactions → "CLOSE_TO_THRESHOLD"
- 201 transactions → "HAS_NEXUS"

### 4.3 Liability Calculation Testing

**Test API Endpoint**:
```bash
# Trigger liability calculation
curl -X POST http://localhost:8000/api/v1/liability/calculate/{analysis_id}

# Get liability estimates
curl http://localhost:8000/api/v1/liability/estimates/{analysis_id}

# Expected response:
{
  "analysis_id": "...",
  "estimates": [
    {
      "state": "CA",
      "taxable_sales": 500000.00,
      "estimated_liability_low": 30000.00,
      "estimated_liability_high": 45000.00,
      "risk_level": "HIGH",
      "recommended_action": "REGISTER_IMMEDIATELY"
    }
  ]
}
```

**Verify Calculations**:
- Taxable sales = gross sales - exempt sales - marketplace sales
- Liability = taxable sales × combined tax rate
- Risk levels based on:
  - Amount of sales over threshold
  - Time period since nexus established
  - Presence of physical locations

### 4.4 Background Job Testing

**Monitor Celery Tasks**:

```bash
# Watch Celery logs in real-time
docker compose logs -f celery-worker

# Expected tasks:
# 1. process_csv_file (CSV upload)
# 2. run_nexus_determination (after profile saved)
# 3. calculate_liability (automatic or manual trigger)
# 4. generate_report (when report requested)
```

**Test Task Failures**:

Trigger errors intentionally:
- Upload corrupt CSV file
- Create analysis without required data
- Expected: Task marked as FAILED, error message recorded

**Check Task Queue**:
```bash
docker compose exec backend python -c "
from workers.celery_app import celery_app

# Get active tasks
inspect = celery_app.control.inspect()
active = inspect.active()
print('Active tasks:', active)

reserved = inspect.reserved()
print('Reserved tasks:', reserved)
"
```

### 4.5 API Endpoint Testing

**Use Interactive Docs**:

Open: http://localhost:8000/docs

Test all endpoints:
- ✓ Authentication: POST `/api/v1/auth/login`
- ✓ CSV Upload: POST `/api/v1/csv/upload`
- ✓ Nexus Rules: GET `/api/v1/nexus/rules`
- ✓ Nexus Results: GET `/api/v1/nexus/results/{analysis_id}`
- ✓ Liability: GET `/api/v1/liability/estimates/{analysis_id}`
- ✓ Reports: POST `/api/v1/reports/generate/{analysis_id}/summary`

---

## Step 5: Bug Documentation

### 5.1 Track Issues

Create a testing log: `docs/PHASE2_TESTING_LOG.md`

```markdown
# Phase 2 Testing Log

## Test Session: 2025-10-22

### Test 1: CSV Upload
- Status: ✓ PASS
- Time: 2 seconds
- Notes: Uploaded 100 rows successfully

### Test 2: Nexus Determination
- Status: ✗ FAIL
- Error: NexusEngine raised KeyError on line 234
- Expected: Calculate nexus for all states
- Actual: Crashed on state 'DE' (no sales tax)
- Fix needed: Handle states without sales tax

### Test 3: Report Generation
- Status: ⚠️ WARNING
- Issue: PDF generation slow (45 seconds for 50 states)
- Notes: Performance optimization needed
```

### 5.2 Common Issues and Fixes

**Issue**: CSV upload fails with 500 error
- **Cause**: File encoding not detected
- **Fix**: Add explicit UTF-8 encoding in `csv_processor.py`

**Issue**: Nexus determination returns 0 results
- **Cause**: No seed data in `nexus_rules` table
- **Fix**: Run `python seeds/nexus_rules_seed.py`

**Issue**: Report generation times out
- **Cause**: Celery task timeout too short
- **Fix**: Increase `task_time_limit` in `celery_app.py`

**Issue**: Frontend shows "Network Error"
- **Cause**: CORS configuration
- **Fix**: Verify `CORS_ORIGINS` in backend `.env`

---

## Sample CSV Format

### Minimal Required Columns

```csv
date,state,amount
2024-01-15,CA,125.00
2024-01-16,NY,250.50
2024-01-17,TX,89.99
```

### Complete Format (Recommended)

```csv
date,state,gross_amount,tax_collected,shipping,is_marketplace,customer_id,order_id
2024-01-15,CA,125.00,10.00,5.00,false,CUST001,ORD12345
2024-01-16,NY,250.50,20.04,0.00,true,CUST002,ORD12346
2024-01-17,TX,89.99,7.42,3.50,false,CUST003,ORD12347
2024-01-18,FL,450.00,0.00,10.00,false,CUST004,ORD12348
2024-01-19,WA,175.25,18.20,0.00,true,CUST005,ORD12349
```

### Column Mapping

The CSV processor supports multiple column name variations:

**Date columns**: `date`, `transaction_date`, `order_date`, `sale_date`, `invoice_date`
**State columns**: `state`, `customer_state`, `ship_to_state`, `billing_state`
**Amount columns**: `amount`, `gross_amount`, `total`, `sale_amount`, `revenue`

---

## Performance Benchmarks

### Expected Processing Times

| Operation | Sample Size | Expected Time |
|-----------|-------------|---------------|
| CSV Upload | 100 rows | < 2 seconds |
| CSV Upload | 1,000 rows | < 5 seconds |
| CSV Upload | 10,000 rows | < 30 seconds |
| Nexus Determination | 100 transactions | < 10 seconds |
| Nexus Determination | 1,000 transactions | < 30 seconds |
| Liability Calculation | 50 states | < 15 seconds |
| PDF Report | 50 states | < 30 seconds |
| Excel Report | 50 states | < 45 seconds |

### Scalability Concerns

**Large CSV Files (100k+ rows)**:
- Consider streaming CSV parser
- Implement batch processing (1,000 rows at a time)
- Add progress updates via WebSocket

**Long Running Tasks**:
- Implement task progress tracking
- Add cancel/pause functionality
- Show estimated time remaining

---

## Success Criteria

Phase 2 is ready for production when:

- ✅ All services start without errors
- ✅ Database migrations run successfully
- ✅ Seed data loads (47 nexus rules, 51 state configs)
- ✅ CSV upload handles 1,000+ rows
- ✅ Nexus determination completes for all 50 states
- ✅ Physical nexus detection works
- ✅ Economic nexus thresholds accurate
- ✅ Liability calculation produces reasonable estimates
- ✅ PDF reports generate successfully
- ✅ Excel reports contain all data
- ✅ All Celery tasks complete without errors
- ✅ Frontend displays results correctly
- ✅ No critical bugs or data corruption
- ✅ Performance meets benchmarks

---

## Next Steps After Testing

1. **Fix Critical Bugs**: Address blocking issues immediately
2. **Performance Optimization**: If benchmarks not met
3. **User Acceptance Testing**: Have stakeholders test
4. **Documentation**: Update user guides
5. **Production Deployment**: Deploy to staging, then production

---

## Support and Troubleshooting

### View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f backend
docker compose logs -f celery-worker
docker compose logs -f frontend

# Database logs
docker compose logs -f postgres
```

### Access Database

```bash
# psql CLI
docker compose exec postgres psql -U postgres -d nexus_analyzer

# List tables
\dt

# Query data
SELECT * FROM analyses ORDER BY created_at DESC LIMIT 5;
SELECT * FROM nexus_results WHERE analysis_id = 'xxx';
```

### Reset Database

```bash
# WARNING: This deletes all data!
docker compose down -v
docker compose up -d
# Then re-run migrations and seeds
```

### Access MinIO Console

1. Open: http://localhost:9001
2. Login with credentials from `.env`
3. Browse buckets: `uploads`, `reports`
4. View/download files

---

**Testing Checklist**: [PHASE2_TESTING_CHECKLIST.md](./PHASE2_TESTING_CHECKLIST.md)
