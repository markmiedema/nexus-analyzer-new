# API Integration Flow Diagram

## Current State (BROKEN)

```
USER FLOW: Create Analysis → Upload CSV → Create Profile → View Results → Generate Reports
                 ↓                ↓              ↓                ↓               ↓

FRONTEND         ✅ Works      ✅ Works      ❌ FAILS           ❌ FAILS        ❌ FAILS
API CALLS        POST /        POST /          POST /            GET /           POST /
                 analyses      analyses/{id}/   business-         reports/        reports/
                              upload           profiles❌        analysis/{id}❌  generate❌

BACKEND          ✅ Works      ✅ Works      ✅ Available       ✅ Available    ✅ Available
ENDPOINTS        POST /        POST /          POST /            GET /           POST /
                 analyses      analyses/{id}/   business-         reports/        reports/
                              upload           profile✅          list/{id}✅      generate/{id}/
                                                                                  summary & detailed✅

ISSUE TYPE       -              -           Path Mismatch     Path Mismatch     Design
                                            + Field Mismatch  + Field Mismatch   Mismatch
```

## Detailed Issue Map

### 1. Business Profile Creation (BROKEN)
```
FRONTEND SENDS:
  POST /api/v1/business-profiles  ❌ Wrong path (plural vs singular)
  {
    business_name: "...",         ❌ Should be: legal_business_name
    business_type: "...",         ❌ Should be: business_structure
    primary_state: "...",         ❌ Not expected by backend
    // MISSING: analysis_id        ❌ Required!
  }

BACKEND EXPECTS:
  POST /api/v1/business-profile   ✅ Correct path (singular)
  {
    analysis_id: "...",           ✅ Required
    legal_business_name: "...",   ✅ Required
    business_structure: "...",    ✅ Optional
    has_physical_presence: bool,  ✅ Optional
    uses_marketplace_facilitators: bool,  ✅ Optional
    sells_tangible_goods: bool    ✅ Optional
  }

RESULT: 404 Not Found, then 422 Validation Error
```

### 2. View Nexus Results (BROKEN)
```
FRONTEND RECEIVES:          BACKEND SENDS:
{                          {
  result_id: "...",          result_id: "...",
  has_physical_nexus: bool,  physical_nexus: bool,      ❌ MISMATCH
  has_economic_nexus: bool,  economic_nexus: bool,      ❌ MISMATCH
  total_sales: number,       total_sales: number,
  ...                        ...
}                          }

FRONTEND CODE:
const summary = {
  physical_nexus_count: results.filter(r => r.has_physical_nexus).length  
  //                                              ^^^^^^^^^^^^^^^^^^^^^^^^
  //                                              → undefined! CAUSES ERROR
}

RESULT: TypeError when accessing properties
```

### 3. View Liability Estimates (BROKEN)
```
FRONTEND EXPECTS:               BACKEND SENDS:
{                              {
  estimate_id: "...",            estimate_id: "...",
  state: "CA",                   state: "CA",
  estimated_liability: 50000,    estimated_liability_low: 45000,    ❌ MISMATCH
  filing_frequency: "monthly",   estimated_liability_mid: 50000,
  ...                            estimated_liability_high: 55000,
}                              }

FRONTEND CODE:
const total = estimates.reduce((sum, e) => sum + e.estimated_liability, 0)
//                                              ^^^^^^^^^^^^^^^^^^^^
//                                              → undefined! CAUSES NaN

RESULT: TypeError, calculations fail, NaN values
```

### 4. Reports List (BROKEN)
```
FRONTEND CALLS:           BACKEND ENDPOINT:
  GET /reports/          ❌ Looking for:
  analysis/{id}          GET /reports/analysis/{id}

                         ✅ Actually provides:
                         GET /reports/list/{id}

RESULT: 404 Not Found
```

### 5. Reports Generate (COMPLETELY DIFFERENT DESIGN)
```
FRONTEND APPROACH (Unified Endpoint):
  POST /reports/generate
  {
    analysis_id: "...",
    report_type: "summary" | "detailed"
  }

BACKEND APPROACH (Separate Endpoints):
  POST /reports/generate/{analysis_id}/summary
  POST /reports/generate/{analysis_id}/detailed

RESULT: 404 Not Found - Backend has no /reports/generate endpoint
```

## Fix Priority Chain

```
Priority 1 - BLOCKING USER FLOW
┌─────────────────────────────────┐
│ Issue #1: Business Profile Path │ ← Remove 's' from endpoints
└─────────────────────────────────┘
                ↓
┌──────────────────────────────────┐
│ Issue #2: Business Profile Fields│ ← Rename/add fields
└──────────────────────────────────┘
                ↓
┌─────────────────────────────────────┐
│ Issue #8: Add analysis_id to request│ ← Include in body
└─────────────────────────────────────┘
                ↓
    ✅ Users can create analyses
                ↓

Priority 2 - VIEW RESULTS BROKEN
┌──────────────────────────────────────┐
│ Issue #6: Rename Nexus Result Fields  │ ← has_physical_nexus
└──────────────────────────────────────┘
                ↓
┌──────────────────────────────────────────────┐
│ Issue #7: Add Liability Estimate Field Alias │ ← estimated_liability
└──────────────────────────────────────────────┘
                ↓
    ✅ Users can see analysis results
                ↓

Priority 3 - REPORTS BROKEN
┌──────────────────────────────────┐
│ Issue #3: Reports List Path       │ ← /analysis → /list
└──────────────────────────────────┘
                ↓
┌────────────────────────────────────────────┐
│ Issue #4: Reports Generate Restructure     │ ← Single endpoint design
└────────────────────────────────────────────┘
                ↓
    ✅ Users can generate reports
```

## Data Type Mismatches Summary

| Field | Frontend Expects | Backend Provides | Fix |
|-------|-----------------|------------------|-----|
| business_name | string | (not sent) | Rename to legal_business_name |
| business_type | string | (not sent) | Rename to business_structure |
| has_physical_nexus | boolean | (field missing) | Rename physical_nexus → has_physical_nexus |
| has_economic_nexus | boolean | (field missing) | Rename economic_nexus → has_economic_nexus |
| estimated_liability | number | (field missing) | Add alias: estimated_liability_mid |
| analysis_id | (not sent) | required UUID | Include in request |
| primary_state | string | (unexpected) | Remove from request |

## Response Format Issues

```
NEXUS RESULTS:
Frontend:        Backend:
{                {
  result_id ✅   result_id ✅
  state ✅        state ✅
  analysis_id ❌ analysis_id ❌ (missing in both!)
  has_physical_nexus ❌  physical_nexus ✅
  has_economic_nexus ❌  economic_nexus ✅
  total_sales ✅  total_sales ✅
  total_transactions ✅ transaction_count ❌ (name mismatch too!)
  created_at ❌  calculated_at ✅ (wrong field)
}                }

LIABILITY ESTIMATES:
Frontend:        Backend:
{                {
  estimate_id ✅ estimate_id ✅
  analysis_id ❌ analysis_id ✅
  state ✅       state ✅
  estimated_liability ❌  estimated_liability_low ✅
                          estimated_liability_mid ✅
                          estimated_liability_high ✅
  filing_frequency ❌    (needs mapping)
  created_at ✅  created_at ✅
}                }
```

## Test Scenarios (Will Currently Fail)

```
Test: User creates new analysis
Step 1: Fill basic info → ✅ Works (Analyses API OK)
Step 2: Upload CSV → ✅ Works (Analyses API OK)
Step 3: Create business profile → ❌ FAILS 
        Error: 404 Not Found (/business-profiles doesn't exist)
Expected: Business profile created
Actual: Request fails, user stuck in wizard

Test: User views analysis results
Step 1: Navigate to analysis detail → ✅ Works
Step 2: Query nexus results → ✅ API returns data
Step 3: Render nexus summary → ❌ CRASHES
        Error: Cannot read property 'length' of undefined
        Reason: trying to access r.has_physical_nexus (doesn't exist)
Expected: Shows "3 states with nexus (2 physical, 1 economic)"
Actual: Page crashes with TypeError

Test: User generates reports
Step 1: Click "Generate Summary" → ✅ Click works
Step 2: API request sent → ❌ 404 Not Found
        Request: POST /reports/generate (wrong endpoint)
Expected: Report generation queued
Actual: User sees error message
```

## Summary: Impact on User Journey

```
USER'S INTENDED JOURNEY        ACTUAL JOURNEY (BROKEN)
┌──────────────────────────┐   ┌──────────────────────────┐
│ 1. Create Analysis      │   │ 1. Create Analysis      │ ✅
├──────────────────────────┤   ├──────────────────────────┤
│ 2. Upload CSV           │   │ 2. Upload CSV           │ ✅
├──────────────────────────┤   ├──────────────────────────┤
│ 3. Create Profile       │   │ 3. Create Profile       │ ❌ 404
├──────────────────────────┤   │ 4. ERROR & RESTART      │
│ 4. View Results         │   │    (must go back)        │
├──────────────────────────┤   └──────────────────────────┘
│ 5. Generate Reports     │
└──────────────────────────┘    IF USER HACKS AROUND ISSUE #3:
                               ┌──────────────────────────┐
      ✅ EXPECTED              │ Create analysis works... │ ✅
                               │ View results...          │
      ❌ ACTUAL                │ → CRASH (TypeError)      │ ❌
                               │ → Reports not available  │ ❌
                               └──────────────────────────┘
```

