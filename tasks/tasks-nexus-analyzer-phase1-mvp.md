# Nexus Analyzer - Phase 1 MVP Task List

Based on: Nexus_Analyzer_Software_Architecture.md

## Relevant Files

### Backend Core
- `backend/main.py` - FastAPI application entry point
- `backend/config.py` - Application configuration and environment variables
- `backend/database.py` - Database connection and session management
- `backend/requirements.txt` - Python dependencies

### Database Models
- `backend/models/tenant.py` - Tenant/Organization model
- `backend/models/user.py` - User model
- `backend/models/analysis.py` - Analysis model
- `backend/models/business_profile.py` - Business profile models
- `backend/models/transaction.py` - Transaction model
- `backend/models/nexus_rule.py` - Nexus rules model
- `backend/models/nexus_result.py` - Nexus determination results
- `backend/models/liability_estimate.py` - Liability estimation model
- `backend/models/state_tax_config.py` - State tax configuration
- `backend/models/report.py` - Report model

### API Routes
- `backend/api/auth.py` - Authentication endpoints
- `backend/api/tenants.py` - Tenant management endpoints
- `backend/api/users.py` - User management endpoints
- `backend/api/analyses.py` - Analysis orchestration endpoints
- `backend/api/csv_processor.py` - CSV upload and processing endpoints
- `backend/api/business_profile.py` - Business profile endpoints
- `backend/api/nexus_rules.py` - Nexus rules endpoints
- `backend/api/reports.py` - Report generation endpoints

### Services
- `backend/services/auth_service.py` - Authentication logic
- `backend/services/csv_processor.py` - CSV parsing and validation
- `backend/services/analysis_service.py` - Analysis orchestration
- `backend/services/nexus_engine.py` - Nexus determination engine
- `backend/services/liability_engine.py` - Liability estimation engine
- `backend/services/report_generator.py` - PDF report generation
- `backend/services/state_tax_service.py` - State tax data service

### Workers
- `backend/workers/celery_app.py` - Celery configuration
- `backend/workers/tasks.py` - Background job tasks

### Frontend Core
- `frontend/package.json` - Frontend dependencies
- `frontend/next.config.js` - Next.js configuration
- `frontend/tsconfig.json` - TypeScript configuration
- `frontend/tailwind.config.js` - Tailwind CSS configuration

### Frontend Pages
- `frontend/app/page.tsx` - Landing/home page
- `frontend/app/login/page.tsx` - Login page
- `frontend/app/dashboard/page.tsx` - Main dashboard
- `frontend/app/analyses/new/page.tsx` - New analysis wizard
- `frontend/app/analyses/[id]/page.tsx` - Analysis detail view

### Frontend Components
- `frontend/components/CSVUpload.tsx` - CSV file upload component
- `frontend/components/BusinessProfileForm.tsx` - Business profile form
- `frontend/components/AnalysisStatus.tsx` - Analysis progress tracker
- `frontend/components/NexusResults.tsx` - Nexus results display
- `frontend/components/LiabilityEstimates.tsx` - Liability estimates display
- `frontend/components/ReportViewer.tsx` - Report preview/download

### Infrastructure
- `docker-compose.yml` - Docker services orchestration
- `backend/Dockerfile` - Backend container definition
- `frontend/Dockerfile` - Frontend container definition
- `.env.example` - Environment variables template
- `alembic.ini` - Database migration configuration
- `alembic/versions/` - Database migration scripts

### Tests
- `backend/tests/test_auth.py` - Authentication tests
- `backend/tests/test_csv_processor.py` - CSV processing tests
- `backend/tests/test_nexus_engine.py` - Nexus engine tests
- `backend/tests/test_liability_engine.py` - Liability engine tests
- `frontend/tests/CSVUpload.test.tsx` - CSV upload component tests

### Notes

- Unit tests should typically be placed alongside the code files they are testing
- Use `pytest` for Python backend tests with `pytest-cov` for coverage
- Use `npm test` or `npx jest` for frontend tests
- Follow the technology stack: Python/FastAPI backend, React/Next.js frontend, PostgreSQL database
- Redis will be used for caching and Celery job queue
- S3-compatible storage (start with local MinIO) for file uploads

## Tasks

- [x] 1.0 Project Infrastructure & Development Environment Setup
  - [x] 1.1 Create project root directory structure (backend/, frontend/, docs/)
  - [x] 1.2 Initialize backend Python project with virtual environment and base requirements.txt (FastAPI, SQLAlchemy, Alembic, psycopg2, Celery, Redis, Pandas, pytest)
  - [x] 1.3 Initialize frontend Next.js project with TypeScript and Tailwind CSS
  - [x] 1.4 Create docker-compose.yml with services: PostgreSQL, Redis, MinIO (S3-compatible), backend, frontend
  - [x] 1.5 Create backend Dockerfile with Python 3.11+ base image
  - [x] 1.6 Create frontend Dockerfile with Node.js base image
  - [x] 1.7 Create .env.example with all required environment variables (DATABASE_URL, REDIS_URL, S3_CONFIG, JWT_SECRET, etc.)
  - [x] 1.8 Set up Alembic for database migrations (alembic init, configure alembic.ini)
  - [x] 1.9 Create basic README.md with project overview and setup instructions
  - [x] 1.10 Test Docker Compose setup - all services should start successfully

- [x] 2.0 Database Schema & Core Data Models
  - [x] 2.1 Create initial Alembic migration for tenants table with columns: tenant_id (UUID, PK), company_name, subdomain, logo_url, primary_color, secondary_color, created_at, subscription_plan, status
  - [x] 2.2 Create Alembic migration for users table with tenant_id FK, email, password_hash, first_name, last_name, role, last_login, created_at
  - [x] 2.3 Create Alembic migration for analyses table with tenant_id FK, created_by FK, client_name, analysis_date, period_start, period_end, status, error_message, timestamps
  - [x] 2.4 Create Alembic migration for business_profiles table linked to analyses
  - [x] 2.5 Create Alembic migration for physical_locations table linked to business_profiles
  - [x] 2.6 Create Alembic migration for transactions table with analysis_id FK, transaction data fields
  - [x] 2.7 Create Alembic migration for nexus_rules table with state, nexus_type, thresholds, effective dates
  - [x] 2.8 Create Alembic migration for nexus_results table with analysis_id FK, state, nexus determination fields
  - [x] 2.9 Create Alembic migration for liability_estimates table with analysis_id FK, state, calculation fields
  - [x] 2.10 Create Alembic migration for state_tax_config table with state configuration data
  - [x] 2.11 Create Alembic migration for reports table with analysis_id FK, report metadata
  - [x] 2.12 Create Alembic migration for audit_log table for tracking all system actions
  - [x] 2.13 Create SQLAlchemy models corresponding to all tables in backend/models/
  - [x] 2.14 Add proper indexes to all tables (tenant_id, state, dates, status fields)
  - [x] 2.15 Run all migrations and verify schema in PostgreSQL

- [x] 3.0 Authentication, Multi-Tenancy & User Management
  - [x] 3.1 Create backend/config.py with Pydantic Settings for environment variables
  - [x] 3.2 Create backend/database.py with SQLAlchemy engine, SessionLocal, and get_db dependency
  - [x] 3.3 Implement JWT token generation and validation in backend/services/auth_service.py
  - [x] 3.4 Create password hashing utilities using bcrypt in auth_service.py
  - [x] 3.5 Implement tenant identification from subdomain/domain in middleware
  - [x] 3.6 Create tenant context manager for filtering all queries by tenant_id
  - [x] 3.7 Implement POST /api/v1/auth/register endpoint for user registration
  - [x] 3.8 Implement POST /api/v1/auth/login endpoint returning JWT token
  - [x] 3.9 Implement GET /api/v1/auth/me endpoint to get current user info
  - [x] 3.10 Create authentication dependency get_current_user for protected routes
  - [x] 3.11 Implement role-based access control (Admin, Analyst, Viewer)
  - [x] 3.12 Create POST /api/v1/tenants endpoint for tenant creation (system admin only)
  - [x] 3.13 Create GET /api/v1/users endpoint to list users in tenant
  - [x] 3.14 Add audit logging for all authentication events
  - [x] 3.15 Write tests for authentication flows (login, token validation, RBAC)

- [x] 4.0 CSV Upload & Processing Pipeline
  - [x] 4.1 Configure MinIO/S3 client in backend for file storage
  - [x] 4.2 Create POST /api/v1/csv/upload endpoint accepting multipart file upload
  - [x] 4.3 Implement file validation (size limits, file type, virus scanning placeholder)
  - [x] 4.4 Store uploaded CSV in S3 with organized path structure (tenant_id/analysis_id/filename)
  - [x] 4.5 Create Celery task for async CSV processing in backend/workers/tasks.py
  - [x] 4.6 Implement CSV parser with encoding detection in backend/services/csv_processor.py
  - [x] 4.7 Implement column name normalization and mapping (date, state, amount aliases)
  - [x] 4.8 Implement data type validation and conversion (dates, amounts, state codes)
  - [x] 4.9 Implement data quality validation (80% valid rows threshold)
  - [x] 4.10 Create batch insert logic for validated transactions into database
  - [x] 4.11 Generate and store validation report with invalid rows
  - [x] 4.12 Update analysis status throughout processing pipeline
  - [x] 4.13 Implement error handling and retry logic for CSV processing
  - [x] 4.14 Create GET /api/v1/csv/templates endpoint to download CSV templates
  - [x] 4.15 Write tests for CSV parsing with various formats and edge cases

- [x] 5.0 Business Profile Management
  - [x] 5.1 Create POST /api/v1/business-profile endpoint to create business profile for analysis
  - [x] 5.2 Create GET /api/v1/business-profile/{id} endpoint to retrieve profile
  - [x] 5.3 Create PUT /api/v1/business-profile/{id} endpoint to update profile
  - [x] 5.4 Implement POST /api/v1/business-profile/{id}/locations endpoint to add physical locations
  - [x] 5.5 Implement DELETE /api/v1/business-profile/{id}/locations/{loc_id} endpoint
  - [x] 5.6 Create validation for business profile data (required fields, valid states, dates)
  - [x] 5.7 Implement logic to determine states with physical presence from locations
  - [x] 5.8 Create service method to extract physical nexus states from business profile
  - [x] 5.9 Handle multiple location types (Office, Warehouse, Retail, Remote Employee)
  - [x] 5.10 Implement business profile form schema validation
  - [x] 5.11 Write tests for business profile CRUD operations

- [x] 6.0 Nexus Rules Engine & Determination Logic
  - [x] 6.1 Seed state_tax_config table with all 50 states' basic tax rate data
  - [x] 6.2 Seed nexus_rules table with economic nexus rules for all 50 states (current as of Oct 2025)
  - [x] 6.3 Create GET /api/v1/nexus-rules endpoint to retrieve all current rules
  - [x] 6.4 Create GET /api/v1/nexus-rules/{state} endpoint for state-specific rules
  - [x] 6.5 Implement physical nexus determination logic in backend/services/nexus_engine.py
  - [x] 6.6 Implement economic nexus threshold checking (sales, transactions, both, either)
  - [x] 6.7 Implement measurement period calculations (Calendar Year, Rolling 12 Months, Previous Calendar Year)
  - [x] 6.8 Implement marketplace facilitator sales filtering logic
  - [x] 6.9 Implement historical nexus establishment date identification
  - [x] 6.10 Calculate confidence levels for nexus determinations (High, Medium, Low)
  - [x] 6.11 Implement registration deadline calculations based on nexus date
  - [x] 6.12 Create Celery task to run nexus determination for an analysis
  - [x] 6.13 Store nexus results in nexus_results table with all determination details
  - [x] 6.14 Implement logic to handle states "close to threshold" warnings
  - [ ] 6.15 Write comprehensive tests for nexus engine with various scenarios

- [x] 7.0 Liability Estimation Engine
  - [x] 7.1 Create backend/services/liability_engine.py with estimation logic
  - [x] 7.2 Implement taxable sales calculation (gross - marketplace - exempt)
  - [x] 7.3 Apply exemption rate assumptions (conservative 10% default)
  - [x] 7.4 Calculate liability range (low: state only, high: state + avg local)
  - [x] 7.5 Implement lookback period calculation based on state rules
  - [x] 7.6 Calculate lookback period liability estimates
  - [x] 7.7 Implement penalty estimation for late registration (10% + monthly interest)
  - [x] 7.8 Create risk assessment scoring algorithm (High, Medium, Low)
  - [x] 7.9 Generate recommendations based on nexus type, liability amount, and risk
  - [x] 7.10 Store liability estimates in liability_estimates table with all assumptions
  - [x] 7.11 Create Celery task to run liability estimation after nexus determination
  - [x] 7.12 Implement POST /api/v1/liability/recalculate with custom assumptions
  - [ ] 7.13 Write tests for liability calculations with various scenarios

- [x] 8.0 Report Generation & PDF Export
  - [x] 8.1 Install WeasyPrint or ReportLab for PDF generation
  - [x] 8.2 Create Jinja2 HTML templates for Executive Summary report
  - [x] 8.3 Create Jinja2 HTML templates for Detailed Analysis report
  - [x] 8.4 Implement CSS styling for professional report appearance
  - [x] 8.5 Create service method to fetch and format all analysis data for reports
  - [x] 8.6 Implement tenant branding application (logo, colors) in report templates
  - [x] 8.7 Generate state-by-state results table with key metrics
  - [ ] 8.8 Add charts/visualizations for nexus states and liability summary
  - [x] 8.9 Include methodology section explaining assumptions and caveats
  - [x] 8.10 Add recommendations section with prioritized action items
  - [x] 8.11 Implement PDF generation from HTML templates
  - [x] 8.12 Store generated PDF in S3 and create report record in database
  - [x] 8.13 Create Celery task for async report generation
  - [x] 8.14 Implement GET /api/v1/reports/{analysis_id}/summary endpoint
  - [x] 8.15 Implement GET /api/v1/reports/{analysis_id}/detailed endpoint
  - [x] 8.16 Create POST /api/v1/reports/{analysis_id}/email endpoint to send report
  - [ ] 8.17 Write tests for report generation with sample data

- [ ] 9.0 Frontend UI - Dashboard, Analysis Workflow & Forms
  - [x] 9.1 Set up Next.js App Router structure with TypeScript
  - [x] 9.2 Configure Tailwind CSS with custom theme (professional color palette)
  - [x] 9.3 Create authentication context and JWT token management
  - [x] 9.4 Create login page (frontend/app/login/page.tsx) with form validation
  - [x] 9.5 Create main dashboard layout with navigation and tenant branding
  - [x] 9.6 Create dashboard home page showing list of recent analyses
  - [x] 9.7 Create "New Analysis" wizard page with multi-step form
  - [x] 9.8 Implement CSV upload component with drag-and-drop (frontend/components/CSVUpload.tsx)
  - [x] 9.9 Create business profile form component with location management
  - [x] 9.10 Implement form validation using React Hook Form + Zod
  - [x] 9.11 Create analysis status tracker component showing progress
  - [x] 9.12 Create analysis detail page displaying nexus results by state
  - [x] 9.13 Create liability estimates display with sortable table
  - [x] 9.14 Implement report viewer/download component
  - [x] 9.15 Add loading states, error handling, and user feedback throughout UI
  - [ ] 9.16 Implement responsive design for mobile/tablet views
  - [x] 9.17 Create API client using React Query for data fetching
  - [ ] 9.18 Write component tests for critical UI components

- [ ] 10.0 Testing, Documentation & MVP Deployment
  - [ ] 10.1 Write integration tests for complete analysis workflow (upload CSV → results)
  - [ ] 10.2 Achieve minimum 70% code coverage for backend services
  - [ ] 10.3 Write API documentation using FastAPI's automatic OpenAPI docs
  - [ ] 10.4 Create deployment guide for Docker Compose production setup
  - [ ] 10.5 Set up environment variable management for production
  - [ ] 10.6 Configure production PostgreSQL with proper connection pooling
  - [ ] 10.7 Configure Redis for production (persistence, memory limits)
  - [ ] 10.8 Set up S3 (AWS/R2/DigitalOcean Spaces) for production file storage
  - [ ] 10.9 Configure Celery workers for production with proper concurrency
  - [ ] 10.10 Set up basic monitoring with health check endpoints
  - [ ] 10.11 Configure logging for production (structured logs, log levels)
  - [ ] 10.12 Create database backup strategy
  - [ ] 10.13 Deploy MVP to staging environment and conduct end-to-end testing
  - [ ] 10.14 Create user documentation for CSV format and analysis process
  - [ ] 10.15 Conduct security review (SQL injection, XSS, CSRF, file upload vulnerabilities)
