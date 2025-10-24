# Quick Fix Summary - API Integration Issues

## All 8 CRITICAL Issues At A Glance

| # | Issue | Status | Error | Fix Difficulty |
|---|-------|--------|-------|-----------------|
| 1 | Business Profile endpoint is `/business-profile` not `/business-profiles` | BLOCKING | 404 | Easy - remove 's' |
| 2 | Business Profile fields wrong: need `analysis_id`, `legal_business_name` instead of `business_name` | BLOCKING | 422 | Easy - rename fields |
| 3 | Reports list endpoint is `/reports/list/{id}` not `/reports/analysis/{id}` | BLOCKING | 404 | Easy - change path |
| 4 | Reports generate is two endpoints `/generate/{id}/summary` not POST `/generate` with body | BLOCKING | 404 | Medium - redesign |
| 5 | Liability calculate endpoint doesn't accept state parameter in URL | LOW PRIORITY | 404 | Easy - remove from unused |
| 6 | NexusResult fields named `physical_nexus` not `has_physical_nexus` | BLOCKING | TypeError | Easy - rename fields |
| 7 | LiabilityEstimate field is `estimated_liability_mid` not `estimated_liability` | BLOCKING | TypeError | Easy - add field alias |
| 8 | Business Profile create missing required `analysis_id` in request | BLOCKING | 422 | Easy - add field |

## Files To Fix (By Priority)

### Priority 1: Core Creation Workflow
- [ ] `/home/user/nexus-analyzer-new/frontend/lib/api.ts` - Lines 139-170 (Issue #1)
- [ ] `/home/user/nexus-analyzer-new/frontend/app/dashboard/analyses/new/page.tsx` - Lines 71-76 (Issues #2, #8)

### Priority 2: Results Display  
- [ ] `/home/user/nexus-analyzer-new/frontend/lib/api.ts` - Lines 29-39 and 41-48 (Issues #6, #7)
- [ ] `/home/user/nexus-analyzer-new/backend/api/nexus_rules.py` - Lines 147-172 (Issue #6)
- [ ] `/home/user/nexus-analyzer-new/backend/api/liability.py` - Lines 98-127 (Issue #7)

### Priority 3: Report Generation
- [ ] `/home/user/nexus-analyzer-new/frontend/lib/api.ts` - Lines 211-222 (Issue #4)
- [ ] `/home/user/nexus-analyzer-new/backend/api/reports.py` - Lines 25-128 (Issue #4)
- [ ] `/home/user/nexus-analyzer-new/frontend/lib/api.ts` - Lines 207-209 (Issue #3)
- [ ] `/home/user/nexus-analyzer-new/backend/api/reports.py` - Lines 133-175 (Issue #3)

## One-Liner Fixes

### Issue #1 - Remove plural 's' from business profile paths
```
OLD: return apiFetch<BusinessProfile[]>('/business-profiles');
NEW: return apiFetch<BusinessProfile[]>('/business-profile');
```

### Issue #2 & #8 - Fix field names and add analysis_id
```typescript
businessProfileApi.create({
  analysis_id: analysisId,  // ADD THIS
  legal_business_name: data.legal_business_name,  // WAS: business_name
  business_structure: data.business_structure,    // WAS: business_type
  has_physical_presence: true,  // ADD THIS
  uses_marketplace_facilitators: false,  // ADD THIS
  sells_tangible_goods: false,  // ADD THIS
})
```

### Issue #3 - Fix reports list path
```
OLD: return apiFetch<Report[]>(`/reports/analysis/${analysisId}`);
NEW: return apiFetch<Report[]>(`/reports/list/${analysisId}`);
```

### Issue #4 - Restructure reports generate
```typescript
// Backend needs single endpoint accepting report_type in body:
// POST /api/v1/reports/generate/{analysis_id}
// { "report_type": "summary" | "detailed" }
```

### Issue #5 - Remove state from liability calculate (not used)
```
Don't worry about this yet - endpoint isn't called from frontend
```

### Issue #6 - Rename nexus fields
```python
# In nexus_rules.py response
OLD: 'physical_nexus': result.physical_nexus
NEW: 'has_physical_nexus': result.physical_nexus
```

### Issue #7 - Add estimated_liability alias
```python
# In liability.py response
ADD: 'estimated_liability': estimate.estimated_liability_mid
KEEP: 'estimated_liability_mid': estimate.estimated_liability_mid
```

## Testing Checklist

After fixes, verify:
- [ ] Create analysis form submits successfully
- [ ] Upload CSV completes
- [ ] Business profile form submits successfully  
- [ ] Analysis detail page loads without errors
- [ ] Nexus results display with data
- [ ] Liability estimates display with data
- [ ] Report generation buttons work
- [ ] Reports list shows generated reports

## Estimated Time: 2-3 hours total

- Paths & field names: ~30 min
- Backend response updates: ~30 min
- Testing & verification: 1-2 hours
