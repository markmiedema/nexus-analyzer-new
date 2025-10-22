# Test Data for Phase 2

This directory contains sample data files for testing the Nexus Analyzer Phase 2 features.

---

## Sample Transaction CSV

**File**: `sample_transactions.csv`

### Overview

- **Rows**: 100 transactions
- **Period**: January 2024 - September 2024 (9 months)
- **States**: CA, NY, TX, FL, WA (5 states)
- **Total Sales**: ~$432,000

### Expected Nexus Results

Based on 2024 economic nexus thresholds:

| State | Threshold | Sample Sales | Expected Determination |
|-------|-----------|--------------|------------------------|
| CA | $500,000 | $175,000 | **CLOSE_TO_THRESHOLD** (~35%) |
| NY | $500,000 | $82,000 | NO_NEXUS (~16%) |
| TX | $100,000 | $75,000 | **CLOSE_TO_THRESHOLD** (~75%) |
| FL | No sales tax | $105,000 | NO_NEXUS |
| WA | $100,000 | $95,000 | **CLOSE_TO_THRESHOLD** (~95%) |

**Note**: If physical locations are added in any state, that state should show **HAS_NEXUS** (physical).

### Data Characteristics

**Revenue Growth**:
- January: ~$17,000
- February: ~$24,000
- March: ~$38,000
- April: ~$54,000
- May: ~$68,000
- June: ~$85,000
- July: ~$92,000
- August: ~$105,000
- September: ~$98,000

**Marketplace Sales**:
- ~10% of transactions marked as `is_marketplace: true`
- States with marketplace facilitator laws should exclude these from nexus calculation

**Product Categories**:
- Electronics (highest revenue)
- Furniture
- Clothing
- Home Goods
- Sports
- Books

**Tax Collection**:
- CA, NY, TX, WA: Tax collected on most transactions
- FL: No tax collected (no state sales tax)
- Amounts vary by state and local rates

### Usage in Testing

#### Test 1: Basic Nexus Determination
- Upload `sample_transactions.csv` without business profile
- Expected: Economic nexus thresholds checked
- Result: TX and WA approaching threshold, CA moderate sales

#### Test 2: Physical Nexus
- Upload `sample_transactions.csv`
- Add physical location in CA (e.g., warehouse)
- Expected: CA shows **HAS_NEXUS** (physical) even though sales < $500k

#### Test 3: Marketplace Facilitator
- Upload `sample_transactions.csv`
- Enable "Uses Marketplace Facilitators" in business profile
- Expected: Marketplace sales excluded from nexus calculation
- Result: Total nexus sales reduced by ~10%

#### Test 4: Threshold Warning
- Upload `sample_transactions.csv`
- Expected: TX and WA flagged as **CLOSE_TO_THRESHOLD**
- UI should show warning: "Approaching nexus in 2 states"

#### Test 5: Report Generation
- Complete full workflow with this CSV
- Generate PDF and Excel reports
- Expected: Reports contain all 100 transactions, grouped by state

#### Test 6: Large File Performance
- Duplicate this CSV 10x or 100x to test scalability
- Expected: System handles 1,000+ or 10,000+ transactions

---

## Creating Custom Test CSVs

### Minimal Format

```csv
date,state,amount
2024-01-01,CA,100.00
2024-01-02,NY,200.00
```

### Complete Format

```csv
date,state,gross_amount,tax_collected,shipping,is_marketplace,customer_id,order_id,product_category
2024-01-01,CA,100.00,8.25,5.00,false,CUST001,ORD001,Electronics
```

### Testing Specific Scenarios

**Test Exact Threshold**:
```csv
date,state,amount
# Create exactly $100,000 in TX sales
2024-01-01,TX,100000.00
```

**Test Transaction Threshold** (for states like AR: 200 transactions):
```csv
# Generate 200 rows with $1 each = $200 total
date,state,amount
2024-01-01,AR,1.00
2024-01-02,AR,1.00
... (repeat 200 times)
```

**Test Multiple States**:
```csv
# Test nexus in all 50 states with $200k each
date,state,amount
2024-01-01,AL,200000.00
2024-01-02,AK,200000.00
... (all 50 states)
```

**Test Invalid Data**:
```csv
# Missing required column (should error)
date,amount
2024-01-01,100.00

# Invalid state code (should error)
date,state,amount
2024-01-01,XX,100.00

# Invalid date (should error)
date,state,amount
invalid-date,CA,100.00
```

---

## Other Test Data Files

Future test files to add:

- `nexus_threshold_test.csv` - Transactions exactly at thresholds
- `multi_state_test.csv` - Sales in all 50 states
- `marketplace_test.csv` - 100% marketplace sales
- `large_file_test.csv` - 10,000+ transactions for performance testing
- `invalid_data_test.csv` - Various validation errors

---

## Expected Test Results Summary

When using `sample_transactions.csv`:

**Nexus Determination**:
- States analyzed: 50
- States with nexus: 0-2 (depending on physical locations)
- States approaching threshold: 2-3 (TX, WA, possibly CA)
- States with no activity: 45

**Liability Estimate** (if nexus exists):
- CA: $14,438 - $21,656 (8.25% state + local)
- TX: $6,188 - $9,281 (8.25% combined)
- WA: $9,835 - $14,753 (10.35% combined)

**Processing Time**:
- CSV upload: < 2 seconds
- Nexus determination: < 5 seconds
- Liability calculation: < 3 seconds
- Report generation: < 30 seconds

---

**Note**: Actual results may vary based on:
- Current date (thresholds measured over calendar year or rolling 12 months)
- Physical locations added in business profile
- Marketplace facilitator settings
- State tax rate changes
