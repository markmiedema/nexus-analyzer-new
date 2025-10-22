# Phase 2: Core Analysis Features - Detailed Plan

**Status**: Planning
**Prerequisites**: Phase 1 Complete ✅
**Estimated Duration**: 4-6 weeks
**Last Updated**: 2025-10-22

---

## Table of Contents

1. [Overview](#overview)
2. [Phase 2 Objectives](#phase-2-objectives)
3. [Architecture Review](#architecture-review)
4. [Task Breakdown](#task-breakdown)
5. [Implementation Timeline](#implementation-timeline)
6. [Success Criteria](#success-criteria)
7. [Risk Assessment](#risk-assessment)

---

## Overview

Phase 2 focuses on implementing the **core business logic** of the Nexus Analyzer application - the features that actually perform sales tax nexus analysis. While Phase 1 built the foundation (auth, database, CI/CD), Phase 2 brings the application's primary value proposition to life.

### What Phase 2 Delivers

By the end of Phase 2, users will be able to:

1. **Upload Transaction Data** - CSV files with sales transactions
2. **Analyze Nexus Obligations** - Automatic determination across all 50 states
3. **View Results** - State-by-state breakdown of nexus obligations
4. **Generate Reports** - PDF/Excel reports for compliance teams
5. **Monitor Status** - Real-time progress tracking for long-running analyses

---

## Phase 2 Objectives

### Primary Goals

1. ✅ **Implement CSV Processing Pipeline**
   - Upload, validate, and parse transaction CSV files
   - Handle large files (100K+ rows) efficiently
   - Provide meaningful error messages for invalid data

2. ✅ **Build Nexus Determination Engine**
   - Physical nexus detection (inventory, employees, property)
   - Economic nexus calculation (sales thresholds by state)
   - Marketplace facilitator logic
   - Click-through nexus detection

3. ✅ **Create Analysis Workflow**
   - Background job processing with Celery
   - Progress tracking and status updates
   - Error handling and retry logic
   - Results storage and retrieval

4. ✅ **Develop Report Generation**
   - PDF summary reports
   - Excel detailed breakdowns
   - State-specific compliance guides
   - Historical report access

5. ✅ **Build Dashboard UI**
   - Analysis listing and filtering
   - Create new analysis wizard
   - Results visualization (charts, maps)
   - Report download interface

### Secondary Goals

- Email notifications for completed analyses
- Bulk analysis comparison
- Saved search filters
- Export data to accounting systems
- Historical trend analysis

---

## Architecture Review

### Current State (Post-Phase 1)

```
┌─────────────────┐
│   Frontend      │  Next.js 15, TypeScript, Tailwind
│   (Port 3000)   │  ✅ Auth flows
│                 │  ✅ Type-safe API client
└────────┬────────┘
         │ HTTP/JSON
┌────────┴────────┐
│   Backend       │  FastAPI, Python 3.11
│   (Port 8000)   │  ✅ Auth endpoints
│                 │  ✅ Database models
│                 │  ✅ Test infrastructure
└────────┬────────┘
         │
    ┌────┴─────┬──────────┬─────────┐
    │          │          │         │
┌───┴────┐ ┌──┴───┐ ┌────┴────┐ ┌─┴──────┐
│ Postgres│ │Redis │ │  MinIO  │ │ Celery │
│ (5432)  │ │(6379)│ │  (9000) │ │ Worker │
└─────────┘ └──────┘ └─────────┘ └────────┘
```

### Phase 2 Additions

```
NEW: CSV Processing Flow
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  Upload  │────→│ Validate │────→│  Parse   │────→│  Store   │
│ CSV File │     │  Format  │     │   Data   │     │  MinIO   │
└──────────┘     └──────────┘     └──────────┘     └──────────┘
                                                           │
                                                           ↓
NEW: Analysis Engine                                  ┌──────────┐
┌──────────┐     ┌──────────┐     ┌──────────┐     │  Celery  │
│  Queue   │────→│ Nexus    │────→│  Save    │────→│   Job    │
│ Analysis │     │  Rules   │     │ Results  │     │(Background)│
└──────────┘     └──────────┘     └──────────┘     └──────────┘

NEW: Report Generation
┌──────────┐     ┌──────────┐     ┌──────────┐
│ Template │────→│ Generate │────→│   Store  │
│  Select  │     │ PDF/Excel│     │  MinIO   │
└──────────┘     └──────────┘     └──────────┘
```

---

## Task Breakdown

### Task 1: CSV Upload & Validation (Week 1)

**Objective**: Allow users to upload transaction CSV files with proper validation

#### Backend Work

**1.1 CSV Schema Definition**
```python
# backend/schemas/csv_upload.py
class TransactionRow(BaseModel):
    date: date
    customer_state: str  # 2-letter state code
    amount: Decimal
    transaction_type: str  # "sale", "refund", etc.
    # ... additional fields
```

**1.2 File Upload Endpoint Enhancement**
- ✅ File size validation (max 50MB)
- ✅ CSV format validation
- ✅ Virus scanning (production)
- ✅ Chunked upload for large files
- ✅ Progress tracking

**1.3 CSV Parsing Service**
```python
# backend/services/csv_processor.py
class CSVProcessor:
    def validate_headers(self, file) -> bool
    def parse_file(self, file) -> List[TransactionRow]
    def detect_encoding(self, file) -> str
    def handle_errors(self, row, errors) -> ValidationError
```

**1.4 Data Quality Checks**
- State code validation (50 states + DC)
- Date format validation
- Amount validation (positive for sales, negative for refunds)
- Required field checks
- Duplicate detection

#### Frontend Work

**1.5 File Upload Component**
```typescript
// frontend/components/CSVUploader.tsx
- Drag-and-drop interface
- File preview before upload
- Progress bar with percentage
- Error display with line numbers
- Download error report
```

**1.6 Validation Feedback UI**
- Real-time validation as file uploads
- Line-by-line error reporting
- Downloadable error CSV
- Fix suggestions for common issues

#### Testing

- Unit tests for CSV parser
- Integration tests for upload endpoint
- E2E test for full upload flow
- Load testing with 100K+ row files

**Estimated Effort**: 5-7 days
**Dependencies**: MinIO configured, Celery working

---

### Task 2: Nexus Determination Engine (Week 2-3)

**Objective**: Implement the core logic for determining nexus obligations

#### 2.1 Nexus Rules Database

**State Configuration**
```python
# backend/models/nexus_rules.py
class StateNexusRule(Base):
    __tablename__ = "state_nexus_rules"

    state_code: str  # "CA", "NY", etc.
    economic_threshold_amount: Decimal  # $500,000 for CA
    economic_threshold_transactions: int  # 200 for many states
    physical_nexus_required: bool
    marketplace_facilitator: bool
    effective_date: date
    notes: str
```

**Seed Data** for all 50 states + DC

#### 2.2 Physical Nexus Detection

```python
# backend/services/nexus/physical.py
class PhysicalNexusDetector:
    def check_inventory_presence(self, state) -> bool
    def check_employee_presence(self, state) -> bool
    def check_property_presence(self, state) -> bool
    def check_sales_representative(self, state) -> bool
```

Data sources:
- Business profile (warehouses, offices)
- Employee data (if available)
- Property records

#### 2.3 Economic Nexus Calculation

```python
# backend/services/nexus/economic.py
class EconomicNexusCalculator:
    def calculate_sales_by_state(self, transactions) -> Dict[str, Decimal]
    def calculate_transaction_count(self, transactions) -> Dict[str, int]
    def check_threshold_exceeded(self, state, sales, count) -> bool
    def get_threshold_date(self, state, sales) -> Optional[date]
```

Logic:
- Aggregate sales by state from CSV
- Count transactions by state
- Compare against state thresholds
- Determine nexus creation date

#### 2.4 Marketplace Facilitator Logic

```python
# backend/services/nexus/marketplace.py
class MarketplaceFacilitatorAnalyzer:
    def identify_marketplace_sales(self, transactions) -> List[Transaction]
    def apply_marketplace_rules(self, state, sales) -> NexusResult
```

Special cases:
- Amazon FBA transactions
- eBay managed payments
- Shopify marketplace

#### 2.5 Nexus Analysis Orchestration

```python
# backend/workers/tasks.py
@celery_app.task
def run_nexus_analysis(analysis_id: str):
    # 1. Load transactions from CSV
    # 2. Run physical nexus check
    # 3. Calculate economic nexus
    # 4. Apply marketplace rules
    # 5. Save results
    # 6. Update analysis status
    # 7. Send notification (if configured)
```

#### Testing

- Unit tests for each nexus type
- State-specific test cases
- Edge case handling (threshold borders)
- Performance testing (100K transactions)
- Historical accuracy validation

**Estimated Effort**: 10-14 days
**Dependencies**: CSV processing complete

---

### Task 3: Analysis Workflow & Status Tracking (Week 3)

**Objective**: Manage analysis lifecycle from creation to completion

#### 3.1 Analysis State Machine

```python
# backend/models/analysis.py
class AnalysisStatus(str, enum.Enum):
    PENDING = "pending"          # Created, not started
    PROCESSING = "processing"    # Celery job running
    COMPLETED = "completed"      # Successfully finished
    FAILED = "failed"            # Error occurred
```

State transitions:
- PENDING → PROCESSING (job starts)
- PROCESSING → COMPLETED (successful)
- PROCESSING → FAILED (error)
- FAILED → PENDING (retry)

#### 3.2 Progress Tracking

```python
# backend/models/analysis.py
class Analysis(Base):
    progress_percent: int  # 0-100
    progress_message: str  # "Processing CA transactions..."
    rows_processed: int
    rows_total: int
    started_at: datetime
    estimated_completion: datetime
```

Updates during processing:
- After each state processed (2% per state)
- After validation complete (10%)
- After calculation complete (80%)

#### 3.3 Error Handling

```python
# backend/services/analysis_service.py
class AnalysisService:
    def handle_error(self, analysis_id, error: Exception):
        # Log error details
        # Update analysis status
        # Optionally retry
        # Notify user
```

Error types:
- CSV parsing errors
- Data validation errors
- Calculation errors
- System errors (DB, S3)

#### 3.4 Retry Logic

```python
@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60
)
def run_nexus_analysis(self, analysis_id):
    try:
        # ... analysis logic
    except Exception as exc:
        raise self.retry(exc=exc)
```

#### Frontend Work

**3.5 Status Tracking Component**
```typescript
// frontend/components/AnalysisProgress.tsx
- Real-time progress bar
- Status message display
- ETA calculation
- Cancel button
- Error display with retry option
```

**3.6 WebSocket/Polling for Updates**
- Poll API every 2s while processing
- Update progress bar
- Show completion notification

**Estimated Effort**: 4-5 days
**Dependencies**: Nexus engine complete

---

### Task 4: Results Storage & Retrieval (Week 4)

**Objective**: Store analysis results efficiently and provide fast retrieval

#### 4.1 Results Schema

```python
# backend/models/nexus_result.py
class NexusResult(Base):
    __tablename__ = "nexus_results"

    result_id: UUID
    analysis_id: UUID
    state: str
    has_physical_nexus: bool
    has_economic_nexus: bool
    nexus_status: str  # "nexus", "no_nexus", "approaching"
    total_sales: Decimal
    total_transactions: int
    nexus_start_date: date
    recommendation: str
```

#### 4.2 Liability Estimation

```python
# backend/models/liability_estimate.py
class LiabilityEstimate(Base):
    result_id: UUID
    estimated_liability: Decimal
    confidence_level: str  # "high", "medium", "low"
    calculation_method: str
    assumptions: str  # JSON
```

Calculation factors:
- State tax rate
- Local tax rates (if applicable)
- Taxable sales percentage
- Filing frequency

#### 4.3 Query Optimization

```python
# Indexes for fast retrieval
Index('ix_nexus_results_analysis', NexusResult.analysis_id)
Index('ix_nexus_results_state', NexusResult.state)
Index('ix_nexus_results_status', NexusResult.nexus_status)
```

#### 4.4 Results API

```python
# backend/api/results.py
@router.get("/analyses/{analysis_id}/results")
def get_results(
    analysis_id: UUID,
    filter_state: Optional[str] = None,
    filter_status: Optional[str] = None
):
    # Return filtered results
```

#### Frontend Work

**4.5 Results Table Component**
```typescript
// frontend/components/ResultsTable.tsx
- Sortable columns
- Filterable by state/status
- Color-coded nexus status
- Expandable rows for details
- Export to CSV
```

**4.6 Results Visualization**
```typescript
// frontend/components/ResultsMap.tsx
- Interactive US map
- Color-coded states (red=nexus, yellow=approaching, green=no nexus)
- Hover tooltips with details
- Click to expand state details
```

**Estimated Effort**: 4-5 days
**Dependencies**: Analysis workflow complete

---

### Task 5: Report Generation (Week 4-5)

**Objective**: Generate professional PDF and Excel reports

#### 5.1 Report Templates

**Summary Report** (PDF)
- Executive summary
- Nexus status by state (table)
- Total liability estimate
- Recommendations
- Next steps

**Detailed Report** (Excel)
- Sheet 1: Summary
- Sheet 2: State-by-state breakdown
- Sheet 3: Transaction details
- Sheet 4: Calculation methodology

#### 5.2 PDF Generation

```python
# backend/services/reports/pdf_generator.py
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

class PDFReportGenerator:
    def generate_summary(self, analysis_id) -> bytes
    def add_header(self, canvas, title)
    def add_state_table(self, canvas, results)
    def add_chart(self, canvas, data)
```

#### 5.3 Excel Generation

```python
# backend/services/reports/excel_generator.py
from openpyxl import Workbook

class ExcelReportGenerator:
    def generate_detailed(self, analysis_id) -> bytes
    def create_summary_sheet(self, workbook, data)
    def create_state_sheet(self, workbook, results)
    def apply_formatting(self, sheet)
```

#### 5.4 Report Storage

```python
# backend/models/report.py
class Report(Base):
    report_id: UUID
    analysis_id: UUID
    report_type: str  # "summary", "detailed"
    file_path: str  # S3 path
    file_size: int
    created_at: datetime
```

Store in MinIO:
- `/reports/{tenant_id}/{analysis_id}/{report_id}.pdf`
- Presigned URLs for download (24hr expiry)

#### Frontend Work

**5.5 Report Download UI**
```typescript
// frontend/components/ReportDownloader.tsx
- Report type selector
- Generate button
- Download progress
- View in browser option
```

**Estimated Effort**: 6-7 days
**Dependencies**: Results retrieval complete

---

### Task 6: Dashboard UI Enhancements (Week 5-6)

**Objective**: Create intuitive, powerful dashboard experience

#### 6.1 Analysis Listing Page

**Features**:
- Paginated table of all analyses
- Filter by status, date range, created by
- Search by business name
- Sort by date, status, total nexus states
- Bulk actions (delete, export)

**Components**:
```typescript
// frontend/app/dashboard/analyses/page.tsx
- AnalysisTable
- FilterPanel
- SearchBar
- PaginationControls
```

#### 6.2 Create Analysis Wizard

**Steps**:
1. Business Information
   - Company name
   - EIN
   - Physical locations (warehouses, offices)
2. Upload Transactions
   - CSV file
   - Validation feedback
3. Review & Start
   - Summary of inputs
   - Estimated time
   - Confirmation

**Components**:
```typescript
// frontend/app/dashboard/analyses/new/page.tsx
- WizardSteps
- BusinessInfoForm
- CSVUploader
- ReviewSummary
```

#### 6.3 Analysis Detail Page

**Sections**:
- Analysis header (status, dates, progress)
- Results summary cards (states with nexus, total liability)
- Interactive map
- State-by-state table
- Generate report section
- Action buttons (re-run, delete, export)

**Components**:
```typescript
// frontend/app/dashboard/analyses/[id]/page.tsx
- AnalysisHeader
- SummaryCards
- ResultsMap
- ResultsTable
- ReportSection
```

#### 6.4 Data Visualization

**Charts**:
- Nexus states over time (trend line)
- Sales by state (bar chart)
- Liability estimate (pie chart by state)
- Threshold proximity (gauge charts)

**Library**: Chart.js or Recharts

#### 6.5 Mobile Responsiveness

- Responsive tables (horizontal scroll on mobile)
- Collapsible filters
- Touch-friendly buttons
- Mobile-optimized charts

**Estimated Effort**: 8-10 days
**Dependencies**: All backend services complete

---

## Implementation Timeline

### Week 1: CSV Processing
- Days 1-2: Backend CSV validation & parsing
- Days 3-4: Frontend upload UI
- Day 5: Integration testing

### Week 2: Nexus Engine (Part 1)
- Days 1-2: State rules database & seeding
- Days 3-4: Physical nexus detection
- Day 5: Economic nexus calculation (initial)

### Week 3: Nexus Engine (Part 2) & Workflow
- Days 1-2: Complete economic nexus
- Day 3: Marketplace facilitator logic
- Days 4-5: Analysis workflow & status tracking

### Week 4: Results & Reports (Part 1)
- Days 1-2: Results storage & retrieval
- Days 3-5: PDF report generation

### Week 5: Reports (Part 2) & Dashboard (Part 1)
- Days 1-2: Excel report generation
- Days 3-5: Analysis listing & filtering

### Week 6: Dashboard (Part 2) & Polish
- Days 1-3: Create analysis wizard
- Days 4-5: Analysis detail page & visualizations

**Total Duration**: 6 weeks (30 working days)
**Contingency**: +1 week for unexpected issues

---

## Success Criteria

### Functional Requirements

✅ Users can upload CSV files up to 50MB
✅ System validates CSV format and data quality
✅ Analysis runs in background without blocking UI
✅ Nexus determination accurate for all 50 states
✅ Results display clearly with visualizations
✅ PDF and Excel reports generate successfully
✅ Download links work with proper authentication

### Performance Requirements

✅ CSV upload completes within 30 seconds (10MB file)
✅ Analysis processes 100K rows in < 5 minutes
✅ Results page loads in < 2 seconds
✅ Report generation completes in < 30 seconds
✅ Dashboard supports 1000+ analyses per tenant

### Quality Requirements

✅ 80%+ test coverage for nexus engine
✅ Zero critical security vulnerabilities
✅ All CI checks passing
✅ Mobile-responsive UI
✅ Accessible (WCAG 2.1 Level AA)

### User Experience

✅ Clear error messages with actionable guidance
✅ Progress indicators for long operations
✅ Intuitive navigation
✅ Consistent design language
✅ Helpful documentation

---

## Risk Assessment

### High Risk

**1. Nexus Rule Complexity**
- **Risk**: State nexus rules are complex and change frequently
- **Mitigation**:
  - Extensive research and documentation
  - Legal review of rules
  - Regular updates to rule database
  - Clear disclaimers about accuracy

**2. Performance at Scale**
- **Risk**: Large CSV files (500K+ rows) may timeout
- **Mitigation**:
  - Chunked processing
  - Streaming CSV parser
  - Database query optimization
  - Background job monitoring

### Medium Risk

**3. Data Quality Issues**
- **Risk**: Poor quality CSV data leads to incorrect results
- **Mitigation**:
  - Comprehensive validation
  - Clear error messages
  - Data quality score
  - Preview before processing

**4. Report Generation Complexity**
- **Risk**: PDF/Excel generation may be fragile
- **Mitigation**:
  - Thorough testing
  - Template versioning
  - Graceful fallbacks
  - Error logging

### Low Risk

**5. UI Complexity**
- **Risk**: Dashboard becomes too complex
- **Mitigation**:
  - User testing
  - Iterative design
  - Progressive disclosure
  - Help documentation

---

## Phase 2 Deliverables

### Code Deliverables

1. **Backend Services**
   - CSV processing service
   - Nexus determination engine
   - Report generation service
   - Analysis workflow orchestration

2. **Frontend Components**
   - CSV uploader
   - Analysis wizard
   - Results dashboard
   - Report viewer

3. **Database**
   - Nexus rules table + seed data
   - Results tables
   - Reports tables
   - Indexes for performance

4. **Background Jobs**
   - Analysis processing job
   - Report generation job
   - Cleanup jobs

### Documentation Deliverables

1. **User Documentation**
   - CSV upload guide
   - Results interpretation guide
   - Report guide
   - FAQ

2. **Technical Documentation**
   - Nexus engine architecture
   - API documentation (updated)
   - Database schema
   - Deployment guide

3. **Testing Documentation**
   - Test plan
   - Test cases
   - Performance benchmarks

### Quality Deliverables

1. **Testing**
   - 80%+ test coverage
   - Integration tests for workflows
   - Performance tests
   - E2E tests for critical paths

2. **CI/CD**
   - All checks passing
   - Automated deployment
   - Performance monitoring

---

## Next Steps

1. **Review this plan** with stakeholders
2. **Prioritize features** if timeline is tight
3. **Set up tracking** (Jira, GitHub Projects, etc.)
4. **Kick off Week 1** with CSV processing
5. **Daily standups** to track progress
6. **Weekly demos** to stakeholders

---

**Ready to build Phase 2?** 🚀

Start with Task 1: CSV Upload & Validation - the foundation for all analysis workflows!
