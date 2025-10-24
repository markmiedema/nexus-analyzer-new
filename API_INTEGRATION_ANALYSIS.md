# Frontend/Backend API Integration Analysis Report

**Date:** 2025-10-24  
**Status:** CRITICAL ISSUES FOUND  
**Impact Level:** WILL BREAK ON FIRST USE

---

## Executive Summary

This codebase has **8 CRITICAL integration issues** that will cause immediate failures when the frontend attempts to communicate with the backend. The issues span across all major API sections (analyses, business-profiles, nexus, liability, and reports).

**Severity Breakdown:**
- **CRITICAL:** 8 issues
- **WARNING:** 0 issues  
- **OK:** 1 section (Analyses API works correctly)

---

## CRITICAL ISSUES

### Issue #1: Business Profile API - Path Mismatch (404 Error)

**Severity:** CRITICAL  
**Type:** Endpoint Path Mismatch  
**Impact:** All business profile operations will fail with 404 Not Found

**Files Involved:**
- Frontend: `/home/user/nexus-analyzer-new/frontend/lib/api.ts` (lines 139-170)
- Backend: `/home/user/nexus-analyzer-new/backend/main.py` (line 47)

**The Problem:**
```
Frontend calls:    GET /api/v1/business-profiles
Backend provides:  GET /api/v1/business-profile  (SINGULAR)
```

The frontend API client expects `/business-profiles` (plural) but the backend router is registered at `/api/v1/business-profile` (singular).

**Affected Endpoints:**
- `businessProfileApi.list()` → `GET /business-profiles` (404)
- `businessProfileApi.get(id)` → `GET /business-profiles/{id}` (404)
- `businessProfileApi.create()` → `POST /business-profiles` (404)
- `businessProfileApi.update()` → `PUT /business-profiles/{id}` (404)
- `businessProfileApi.delete()` → `DELETE /business-profiles/{id}` (404)

**Fix Required:** Change frontend API calls from `/business-profiles` to `/business-profile`

```typescript
// Change all endpoints in api.ts lines 139-170
export const businessProfileApi = {
  list: async (): Promise<BusinessProfile[]> => {
    return apiFetch<BusinessProfile[]>('/business-profile');  // Remove 's'
  },
  get: async (id: string): Promise<BusinessProfile> => {
    return apiFetch<BusinessProfile>(`/business-profile/${id}`);  // Remove 's'
  },
  // ... etc for create, update, delete
};
```

---

### Issue #2: Business Profile Create - Request Body Field Mismatch (422 Error)

**Severity:** CRITICAL  
**Type:** Request Payload Mismatch  
**Impact:** Business profile creation will fail with validation errors

**Files Involved:**
- Frontend: `/home/user/nexus-analyzer-new/frontend/app/dashboard/analyses/new/page.tsx` (lines 71-76)
- Backend: `/home/user/nexus-analyzer-new/backend/api/business_profile.py` (lines 31-79)
- Schema: `/home/user/nexus-analyzer-new/backend/schemas/business_profile.py` (referenced in business_profile.py line 16)

**The Problem:**

Frontend sends:
```json
{
  "business_name": "Acme Corp",
  "business_type": "LLC",
  "primary_state": "CA"
}
```

Backend expects (via BusinessProfileCreate schema):
```python
{
  "analysis_id": "required-uuid",
  "legal_business_name": "required-string",
  "business_structure": "optional-string",
  "has_physical_presence": "optional-boolean",
  "uses_marketplace_facilitators": "optional-boolean",
  "sells_tangible_goods": "optional-boolean"
}
```

**Specific Issues:**
1. **Missing `analysis_id`**: Frontend doesn't send this required field
2. **Wrong field name**: Frontend sends `business_name` but backend expects `legal_business_name`
3. **Wrong field name**: Frontend sends `business_type` but backend expects `business_structure`
4. **Unused field**: Frontend sends `primary_state` but backend doesn't expect it

**Error Response Expected:** `422 Unprocessable Entity - validation error`

**Fix Required:** Update the NewAnalysisPage component (lines 71-76):

```typescript
// Instead of:
const createProfileMutation = useMutation({
  mutationFn: ({ analysisId, data }: { analysisId: string; data: BusinessProfileFormData }) =>
    businessProfileApi.create({
      business_name: data.legal_business_name || data.doing_business_as || '',
      business_type: data.business_structure,
      primary_state: data.locations?.[0]?.state_code,
    }),

// Change to:
const createProfileMutation = useMutation({
  mutationFn: ({ analysisId, data }: { analysisId: string; data: BusinessProfileFormData }) =>
    businessProfileApi.create({
      analysis_id: analysisId,  // Add this!
      legal_business_name: data.legal_business_name || data.doing_business_as || '',
      business_structure: data.business_structure,
      has_physical_presence: (data.locations && data.locations.length > 0) || false,
      uses_marketplace_facilitators: data.uses_marketplace_facilitators || false,
      sells_tangible_goods: false,  // Add this field
    }),
```

Also update the API type definition:

```typescript
// In api.ts lines 148-153
create: async (data: Partial<BusinessProfile>): Promise<BusinessProfile> => {
  // This needs to accept analysis_id
```

---

### Issue #3: Reports List - Path Mismatch (404 Error)

**Severity:** CRITICAL  
**Type:** Endpoint Path Mismatch  
**Impact:** Fetching list of reports will fail with 404

**Files Involved:**
- Frontend: `/home/user/nexus-analyzer-new/frontend/lib/api.ts` (lines 207-209)
- Backend: `/home/user/nexus-analyzer-new/backend/api/reports.py` (lines 133-175)

**The Problem:**
```
Frontend calls:    GET /api/v1/reports/analysis/{analysisId}
Backend provides:  GET /api/v1/reports/list/{analysis_id}
```

**Error Response Expected:** `404 Not Found`

**Fix Required:** Option A - Change frontend to match backend:

```typescript
// In api.ts line 208
list: async (analysisId: string): Promise<Report[]> => {
  return apiFetch<Report[]>(`/reports/list/${analysisId}`);  // Change 'analysis' to 'list'
},
```

**OR** Option B - Change backend to match frontend (preferred):

```python
# In reports.py line 133
@router.get("/analysis/{analysis_id}", response_model=List[dict])  # Change from /list/ to /analysis/
async def list_reports(
```

---

### Issue #4: Reports Generate - API Structure Completely Different (404 Error)

**Severity:** CRITICAL  
**Type:** API Design Mismatch  
**Impact:** Report generation will fail completely

**Files Involved:**
- Frontend: `/home/user/nexus-analyzer-new/frontend/lib/api.ts` (lines 211-222)
- Frontend Component: `/home/user/nexus-analyzer-new/frontend/components/ReportViewer.tsx` (lines 27-54)
- Backend: `/home/user/nexus-analyzer-new/backend/api/reports.py` (lines 25-128)

**The Problem:**

Frontend approach (unified endpoint with query parameter):
```typescript
reportsApi.generate(analysisId, 'summary')
// Sends: POST /api/v1/reports/generate
// Body: { analysis_id: "...", report_type: "summary" }
```

Backend approach (separate endpoints with analysis_id in path):
```python
@router.post("/generate/{analysis_id}/summary")  # POST /api/v1/reports/generate/{analysis_id}/summary
@router.post("/generate/{analysis_id}/detailed") # POST /api/v1/reports/generate/{analysis_id}/detailed
```

**Error Response Expected:** `404 Not Found` when frontend calls `/reports/generate` with no analysis_id

**Fix Required:** Option A - Refactor backend to have single endpoint (RECOMMENDED):

```python
# In reports.py - replace the two separate endpoints with one:
@router.post("/generate/{analysis_id}", status_code=status.HTTP_202_ACCEPTED)
async def generate_report(
    analysis_id: UUID,
    request_body: dict = Body(...),  # { "report_type": "summary" | "detailed" }
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    report_type = request_body.get('report_type', 'summary')
    # ... rest of logic shared between both
```

**OR** Option B - Update frontend to match backend:

```typescript
generate: async (
  analysisId: string,
  reportType: 'summary' | 'detailed'
): Promise<Report> => {
  const endpoint = reportType === 'summary' 
    ? `/reports/generate/${analysisId}/summary`
    : `/reports/generate/${analysisId}/detailed`;
  return apiFetch<Report>(endpoint, { method: 'POST' });
},
```

---

### Issue #5: Liability Calculate - State Parameter Missing (404 Error)

**Severity:** CRITICAL  
**Type:** Endpoint Path Mismatch  
**Impact:** Per-state liability calculation will fail

**Files Involved:**
- Frontend: `/home/user/nexus-analyzer-new/frontend/lib/api.ts` (lines 192-202)
- Backend: `/home/user/nexus-analyzer-new/backend/api/liability.py` (lines 321-375)

**The Problem:**
```
Frontend calls:    POST /api/v1/liability/calculate/{analysisId}/{state}
Backend provides:  POST /api/v1/liability/calculate/{analysis_id}
```

The frontend expects to pass state as a URL parameter, but the backend endpoint doesn't accept it.

**Error Response Expected:** `404 Not Found` (backend will try to parse `{state}` as something else)

**Fix Required:** Update frontend to match backend:

```typescript
// In api.ts lines 192-202
calculateEstimate: async (
  analysisId: string,
  state: string
): Promise<LiabilityEstimate> => {
  // Option 1: Pass state as query parameter
  return apiFetch<LiabilityEstimate>(
    `/liability/calculate/${analysisId}?state=${state}`,
    { method: 'POST' }
  );
  
  // OR Option 2: Include state in request body
  return apiFetch<LiabilityEstimate>(
    `/liability/calculate/${analysisId}`,
    {
      method: 'POST',
      body: JSON.stringify({ state })
    }
  );
},
```

**Note:** The `calculateEstimate` endpoint doesn't appear to be used in the current frontend code (searches show no usage), so this may be a lower priority if not used.

---

### Issue #6: NexusResult Response Fields - Name Mismatch (TypeError)

**Severity:** CRITICAL  
**Type:** Response Field Name Mismatch  
**Impact:** Frontend will fail when accessing nexus result properties

**Files Involved:**
- Frontend Type: `/home/user/nexus-analyzer-new/frontend/lib/api.ts` (lines 29-39)
- Frontend Usage: `/home/user/nexus-analyzer-new/frontend/app/dashboard/analyses/[id]/page.tsx` (lines 56-60)
- Backend Response: `/home/user/nexus-analyzer-new/backend/api/nexus_rules.py` (lines 147-172)

**The Problem:**

Frontend expects:
```typescript
export interface NexusResult {
  has_physical_nexus: boolean;  // ← Field name
  has_economic_nexus: boolean;  // ← Field name
  // ...
}
```

Backend returns:
```python
{
  'physical_nexus': result.physical_nexus,      # ← Different name (no 'has_' prefix)
  'economic_nexus': result.economic_nexus,      # ← Different name (no 'has_' prefix)
  // ...
}
```

**Usage Error Location (lines 56-60 of [id]/page.tsx):**
```typescript
const nexusSummary = nexusResults ? {
  total_nexus_states: nexusResults.length,
  physical_nexus_count: nexusResults.filter(r => r.has_physical_nexus).length,  // ← ERROR: undefined
  economic_nexus_count: nexusResults.filter(r => r.has_economic_nexus).length,  // ← ERROR: undefined
}
```

**Error Response:** `Cannot read property 'length' of undefined`

**Fix Required:** Option A - Update backend to match frontend naming (RECOMMENDED):

```python
# In nexus_rules.py lines 147-172
return [
  {
    'result_id': str(result.result_id),
    'state': result.state,
    'analysis_id': str(result.analysis_id),  # Also add this if missing
    'has_physical_nexus': result.physical_nexus,  # Add 'has_' prefix
    'has_economic_nexus': result.economic_nexus,  # Add 'has_' prefix
    'nexus_status': result.nexus_status.value,
    # ... rest of fields
  }
  for result in results
]
```

**OR** Option B - Update frontend type and all usages:

```typescript
// In api.ts
export interface NexusResult {
  physical_nexus: boolean;   // Change from has_physical_nexus
  economic_nexus: boolean;   // Change from has_economic_nexus
  // ...
}

// Then update all usages in [id]/page.tsx
physical_nexus_count: nexusResults.filter(r => r.physical_nexus).length,
economic_nexus_count: nexusResults.filter(r => r.economic_nexus).length,
```

---

### Issue #7: LiabilityEstimate Response Fields - Multiple Field Names Mismatch (TypeError)

**Severity:** CRITICAL  
**Type:** Response Field Name Mismatch  
**Impact:** Frontend will fail when accessing liability estimates

**Files Involved:**
- Frontend Type: `/home/user/nexus-analyzer-new/frontend/lib/api.ts` (lines 41-48)
- Frontend Usage: `/home/user/nexus-analyzer-new/frontend/app/dashboard/analyses/[id]/page.tsx` (lines 62-70)
- Backend Response: `/home/user/nexus-analyzer-new/backend/api/liability.py` (lines 98-127)

**The Problem:**

Frontend expects:
```typescript
export interface LiabilityEstimate {
  estimate_id: string;
  analysis_id: string;
  state: string;
  estimated_liability: number;        // ← Single field
  filing_frequency?: string;
  created_at: string;
}
```

Backend returns:
```python
{
  'estimate_id': str(estimate.estimate_id),
  'state': estimate.state,
  'estimated_liability_low': estimate.estimated_liability_low,      # ← Three separate fields
  'estimated_liability_mid': estimate.estimated_liability_mid,
  'estimated_liability_high': estimate.estimated_liability_high,
  # ... other fields
}
```

**Usage Error Location (lines 62-70 of [id]/page.tsx):**
```typescript
const liabilitySummary = liabilityEstimates ? {
  total_liability_mid: liabilityEstimates.reduce((sum, est) => sum + (est.estimated_liability || 0), 0),
  //                                                                    ^^^^^^^^^^^^^^^^^ → undefined!
  high_risk_count: liabilityEstimates.filter(est => est.estimated_liability > 10000).length,
  //                                               ^^^^^^^^^^^^^^^^^ → undefined!
}
```

**Error Response:** `TypeError: Cannot read property of undefined` or `NaN` in calculations

**Fix Required:** Option A - Update backend to provide simplified view (RECOMMENDED):

```python
# In liability.py lines 98-127
return [
  {
    'estimate_id': str(estimate.estimate_id),
    'analysis_id': str(estimate.analysis_id),
    'state': estimate.state,
    # Provide a single field for basic usage
    'estimated_liability': estimate.estimated_liability_mid,  # Add this
    'estimated_liability_low': estimate.estimated_liability_low,
    'estimated_liability_mid': estimate.estimated_liability_mid,
    'estimated_liability_high': estimate.estimated_liability_high,
    'filing_frequency': 'TBD',  # Map from appropriate field
    'created_at': estimate.created_at.isoformat(),
    # ... rest of fields
  }
  for estimate in estimates
]
```

**OR** Option B - Update frontend type and usages:

```typescript
// In api.ts
export interface LiabilityEstimate {
  estimate_id: string;
  analysis_id: string;
  state: string;
  estimated_liability_low: number;
  estimated_liability_mid: number;
  estimated_liability_high: number;
  // ... other fields
}

// Then update [id]/page.tsx usages:
total_liability_mid: liabilityEstimates.reduce((sum, est) => sum + (est.estimated_liability_mid || 0), 0),
high_risk_count: liabilityEstimates.filter(est => est.estimated_liability_mid > 10000).length,
```

---

### Issue #8: Business Profile Missing analysis_id Parameter Validation (422 Error)

**Severity:** CRITICAL  
**Type:** Missing Required Parameter  
**Impact:** Creating a business profile will fail validation

**Files Involved:**
- Frontend: `/home/user/nexus-analyzer-new/frontend/app/dashboard/analyses/new/page.tsx` (lines 71-76)
- Backend: `/home/user/nexus-analyzer-new/backend/api/business_profile.py` (lines 31-79)

**The Problem:**

The backend endpoint requires `analysis_id` to verify that the analysis exists and belongs to the user's tenant (line 49):

```python
analysis = db.query(Analysis).filter(
    Analysis.analysis_id == profile_data.analysis_id,  # ← Expects this field
    Analysis.tenant_id == current_user.tenant_id
).first()
```

But the frontend doesn't send it in the create request (lines 72-76 of new/page.tsx):

```typescript
businessProfileApi.create({
  business_name: data.legal_business_name || data.doing_business_as || '',
  business_type: data.business_structure,
  primary_state: data.locations?.[0]?.state_code,
  // ↑ No analysis_id sent!
})
```

**Error Response Expected:** `422 Unprocessable Entity - validation error: "analysis_id is required"`

**Fix Required:** Send `analysis_id` with the create request:

```typescript
// In analyses/new/page.tsx lines 71-76
const createProfileMutation = useMutation({
  mutationFn: ({ analysisId, data }: { analysisId: string; data: BusinessProfileFormData }) =>
    businessProfileApi.create({
      analysis_id: analysisId,  // ← ADD THIS
      legal_business_name: data.legal_business_name || data.doing_business_as || '',
      business_structure: data.business_structure,
      has_physical_presence: (data.locations && data.locations.length > 0) || false,
      uses_marketplace_facilitators: data.uses_marketplace_facilitators || false,
      sells_tangible_goods: false,
    }),
```

---

## WORKING CORRECTLY

### Analyses API - OK

**Status:** ✅ No Issues Found

**Endpoints:**
- `analysesApi.list()` → `GET /api/v1/analyses` ✅
- `analysesApi.get(id)` → `GET /api/v1/analyses/{id}` ✅
- `analysesApi.create(data)` → `POST /api/v1/analyses` ✅
- `analysesApi.delete(id)` → `DELETE /api/v1/analyses/{id}` ✅
- `analysesApi.uploadCSV()` → `POST /api/v1/analyses/{id}/upload` ✅

All request/response structures align correctly.

---

## API COMPATIBILITY MATRIX

| Section | Frontend Endpoint | Backend Endpoint | Path Match | Fields Match | Overall |
|---------|------------------|------------------|-----------|--------------|---------|
| **Analyses** | `/analyses` | `/analyses` | ✅ YES | ✅ YES | ✅ OK |
| **Business Profile** | `/business-profiles` | `/business-profile` | ❌ NO | ❌ NO | ❌ BROKEN |
| **Nexus Results** | `/nexus/results/{id}` | `/nexus/results/{id}` | ✅ YES | ❌ NO | ❌ BROKEN |
| **Liability Calc** | `/liability/calculate/{id}/{state}` | `/liability/calculate/{id}` | ❌ NO | N/A | ❌ BROKEN |
| **Reports List** | `/reports/analysis/{id}` | `/reports/list/{id}` | ❌ NO | N/A | ❌ BROKEN |
| **Reports Generate** | `/reports/generate` (POST body) | `/reports/generate/{id}/summary` | ❌ NO | N/A | ❌ BROKEN |

---

## PRIORITY FIX ORDER

1. **FIRST (Frontend Creation Wizard):** Fix Issues #1, #2, #8 - These block the core user workflow
2. **SECOND (View Results):** Fix Issues #6, #7 - These block viewing analysis results
3. **THIRD (Report Generation):** Fix Issues #3, #4 - These block report generation
4. **OPTIONAL:** Fix Issue #5 - State-specific liability calculation (appears unused)

---

## ESTIMATED REMEDIATION TIME

- **Fix All CRITICAL Issues:** 2-3 hours
  - API path corrections: 30 minutes
  - Field name updates: 30 minutes
  - Testing updates: 1-2 hours
  
---

## TESTING RECOMMENDATIONS

After fixes are applied, test these user workflows:

1. **Create Analysis** - Verify form submission succeeds
2. **Upload CSV** - Verify file upload works
3. **Create Business Profile** - Verify profile creation succeeds
4. **View Analysis Results** - Verify nexus/liability data displays correctly
5. **Generate Reports** - Verify report generation initiates

Use browser DevTools Network tab to verify HTTP requests match expected paths and payloads.

