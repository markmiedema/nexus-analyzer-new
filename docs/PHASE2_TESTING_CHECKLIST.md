# Phase 2 Testing Checklist

**Date**: _____________
**Tester**: _____________
**Environment**: _____________

---

## Pre-Test Setup

- [ ] Docker services running (`docker compose ps`)
- [ ] Database migrations applied (`alembic upgrade head`)
- [ ] Nexus rules seeded (47 states)
- [ ] State tax config seeded (51 jurisdictions)
- [ ] Demo user created
- [ ] MinIO accessible (http://localhost:9001)
- [ ] Backend API healthy (http://localhost:8000/health)
- [ ] Frontend accessible (http://localhost:3000)
- [ ] Celery worker running

---

## Test 1: Authentication & Authorization

- [ ] Login with demo credentials works
- [ ] Dashboard loads after login
- [ ] Logout works
- [ ] Invalid credentials rejected
- [ ] Protected routes require authentication

**Notes**:
```





```

---

## Test 2: CSV Upload & Validation

### Test 2.1: Valid CSV Upload

- [ ] "New Analysis" button visible on dashboard
- [ ] Basic info form accepts valid data
- [ ] Analysis created in database
- [ ] CSV file selection works
- [ ] Upload progress displayed
- [ ] File uploaded to MinIO
- [ ] Celery task `process_csv_file` triggered
- [ ] Transactions imported to database
- [ ] No errors in Celery logs

**CSV Used**: _____________
**Rows**: _____________
**Processing Time**: _____________

**Notes**:
```





```

### Test 2.2: CSV Validation

- [ ] Missing required column → Error message
- [ ] Invalid state code → Warning/error
- [ ] Invalid date format → Handled gracefully
- [ ] Empty file → Error message
- [ ] Very large file (10k+ rows) → Processes successfully

**Notes**:
```





```

---

## Test 3: Nexus Determination

### Test 3.1: Economic Nexus

- [ ] CA: $500k threshold checked correctly
- [ ] TX: $100k threshold checked correctly
- [ ] States with transaction thresholds work (AR, CT)
- [ ] "CLOSE_TO_THRESHOLD" status when 90%+ of threshold
- [ ] "HAS_NEXUS" when threshold exceeded
- [ ] "NO_NEXUS" when below threshold
- [ ] Confidence level calculated (HIGH/MEDIUM/LOW)

**Test Data**:
- State: _____________
- Sales: _____________
- Expected Nexus: _____________
- Actual Nexus: _____________

**Notes**:
```





```

### Test 3.2: Physical Nexus

- [ ] Business profile with physical locations saved
- [ ] Physical nexus detected for location states
- [ ] Multiple locations in same state handled
- [ ] Closed locations (with end date) excluded
- [ ] Employee locations trigger nexus
- [ ] Inventory locations trigger nexus

**Locations Tested**: _____________

**Notes**:
```





```

### Test 3.3: Marketplace Facilitator

- [ ] Marketplace facilitator flag respected
- [ ] Marketplace sales excluded in states with MF laws
- [ ] Marketplace sales included in states without MF laws
- [ ] Multiple marketplace facilitators handled

**Notes**:
```





```

---

## Test 4: Liability Calculation

- [ ] `calculate_liability` API endpoint works
- [ ] Liability calculated for all nexus states
- [ ] Formula: taxable_sales × combined_tax_rate
- [ ] Exempt sales excluded
- [ ] Marketplace sales excluded (where applicable)
- [ ] Risk level assigned (HIGH/MEDIUM/LOW)
- [ ] Recommended action provided
- [ ] Low/high estimates reasonable

**Sample Calculation**:
- State: _____________
- Taxable Sales: _____________
- Tax Rate: _____________
- Calculated Liability: _____________
- Risk Level: _____________

**Notes**:
```





```

---

## Test 5: Analysis Results Display

### Test 5.1: Results Table

- [ ] All 50 states displayed in table
- [ ] Nexus status column correct
- [ ] Sales amounts formatted correctly
- [ ] Transaction counts accurate
- [ ] Threshold percentages calculated
- [ ] Sorting by column works
- [ ] Filtering by nexus status works
- [ ] Color coding for status (red/yellow/green)

**Notes**:
```





```

### Test 5.2: Status Tracking

- [ ] Status badge displays current state
- [ ] Status timeline/progress bar shown
- [ ] Timestamps displayed correctly
- [ ] Error messages shown if failed
- [ ] Real-time updates (if applicable)

**Notes**:
```





```

---

## Test 6: Report Generation

### Test 6.1: PDF Summary Report

- [ ] "Generate Summary Report" button works
- [ ] Report generation task triggered
- [ ] Generation completes in < 60 seconds
- [ ] Download link appears
- [ ] PDF file downloads successfully
- [ ] PDF contains:
  - [ ] Executive summary
  - [ ] Nexus determination summary
  - [ ] States requiring registration
  - [ ] Liability estimate
  - [ ] Recommendations
  - [ ] Charts/visualizations
- [ ] Professional formatting
- [ ] No missing data or errors

**Generation Time**: _____________

**Notes**:
```





```

### Test 6.2: Excel Detailed Report

- [ ] "Generate Detailed Report" button works
- [ ] Excel file downloads successfully
- [ ] Contains sheets:
  - [ ] Summary
  - [ ] Nexus Results
  - [ ] Liability Estimates
  - [ ] Transaction Details
  - [ ] Recommendations
- [ ] Data accurate in all sheets
- [ ] Formulas work (if any)
- [ ] Formatting readable

**Generation Time**: _____________

**Notes**:
```





```

---

## Test 7: Background Jobs (Celery)

- [ ] `process_csv_file` task completes successfully
- [ ] `run_nexus_determination` task completes successfully
- [ ] `calculate_liability` task completes successfully
- [ ] `generate_report` task completes successfully
- [ ] Task failures handled gracefully
- [ ] Error messages logged
- [ ] Analysis status updated correctly
- [ ] No stuck/zombie tasks

**Task Execution Times**:
- CSV processing: _____________
- Nexus determination: _____________
- Liability calculation: _____________
- Report generation: _____________

**Notes**:
```





```

---

## Test 8: Error Handling

### Test 8.1: API Errors

- [ ] 400 Bad Request for invalid input
- [ ] 401 Unauthorized for missing auth
- [ ] 404 Not Found for missing resources
- [ ] 500 Internal Server Error handled gracefully
- [ ] Error messages helpful and clear

**Notes**:
```





```

### Test 8.2: Frontend Errors

- [ ] Network errors displayed to user
- [ ] Validation errors shown inline
- [ ] Loading states shown during async operations
- [ ] Error boundaries prevent crashes
- [ ] Toast notifications for errors

**Notes**:
```





```

---

## Test 9: Performance

### Test 9.1: Upload Performance

| Rows | Upload Time | Processing Time | Total Time |
|------|-------------|-----------------|------------|
| 100  |             |                 |            |
| 1,000|             |                 |            |
| 10,000|            |                 |            |

**Meets Benchmarks?**: _____________

### Test 9.2: Analysis Performance

- [ ] Nexus determination < 30 seconds (1,000 transactions)
- [ ] Liability calculation < 15 seconds (50 states)
- [ ] Page load times < 2 seconds
- [ ] No memory leaks
- [ ] No database connection issues

**Notes**:
```





```

---

## Test 10: Data Integrity

- [ ] Transaction data matches CSV exactly
- [ ] No duplicate transactions imported
- [ ] Date formats consistent
- [ ] Amounts stored with correct precision (2 decimals)
- [ ] State codes normalized (uppercase)
- [ ] Foreign key relationships maintained
- [ ] Cascade deletes work correctly
- [ ] Audit log captures all changes

**Notes**:
```





```

---

## Test 11: Multi-Tenant Isolation

- [ ] Users only see their tenant's data
- [ ] Analyses scoped to tenant
- [ ] Reports scoped to tenant
- [ ] Cross-tenant access blocked
- [ ] Tenant ID in all API responses

**Notes**:
```





```

---

## Test 12: Security

- [ ] Passwords hashed (not stored plaintext)
- [ ] JWT tokens expire appropriately
- [ ] SQL injection prevented (parameterized queries)
- [ ] XSS prevented (input sanitization)
- [ ] CSRF protection enabled
- [ ] File upload size limits enforced
- [ ] File type validation (CSV only)
- [ ] API rate limiting works

**Notes**:
```





```

---

## Bugs Found

### Bug #1
- **Severity**: Critical / High / Medium / Low
- **Component**: _____________
- **Description**:
  ```



  ```
- **Steps to Reproduce**:
  ```
  1.
  2.
  3.
  ```
- **Expected**: _____________
- **Actual**: _____________
- **Fix**: _____________

### Bug #2
- **Severity**: Critical / High / Medium / Low
- **Component**: _____________
- **Description**:
  ```



  ```

### Bug #3
- **Severity**: Critical / High / Medium / Low
- **Component**: _____________
- **Description**:
  ```



  ```

---

## Summary

**Total Tests**: _________ / 12 sections
**Tests Passed**: _________
**Tests Failed**: _________
**Bugs Found**: _________
- Critical: _________
- High: _________
- Medium: _________
- Low: _________

**Overall Status**: ✅ READY FOR PRODUCTION / ⚠️ NEEDS FIXES / ❌ BLOCKED

**Recommended Next Steps**:
```





```

**Sign-off**:
- Tester: _________________________ Date: _____________
- Reviewer: _______________________ Date: _____________
