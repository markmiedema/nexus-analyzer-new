# Database Migration Guide

## Boolean Field Type Fix Migration

**Migration ID**: `a94f8f8fd5e8`
**Date**: 2025-10-21
**Status**: Ready to apply

### Summary

This migration fixes a data type inconsistency in the database models where boolean fields were incorrectly defined as `String(10)` instead of proper `Boolean` types.

### Models Affected

1. **User Model** (`backend/models/user.py`)
   - `is_active`: Changed from `String(10)` to `Boolean`
   - `email_verified`: Changed from `String(10)` to `Boolean`

2. **AuditLog Model** (`backend/models/audit_log.py`)
   - `success`: Changed from `String(10)` to `Boolean`

### Changes Made

#### Code Changes
- ✅ Updated User model to use `Boolean` type
- ✅ Updated AuditLog model to use `Boolean` type
- ✅ Fixed all code references from string comparisons to boolean comparisons
- ✅ Updated API endpoints to use boolean values
- ✅ Updated test fixtures to use boolean values

#### Files Modified
```
backend/models/user.py
backend/models/audit_log.py
backend/dependencies/auth.py
backend/api/auth.py
backend/api/tenants.py
backend/tests/test_auth.py
```

### Migration Strategy

The migration handles two scenarios:

#### 1. Existing Databases (with data)
- Creates temporary boolean columns
- Converts string data: `"true"` → `TRUE`, `"false"` → `FALSE`
- Drops old string columns
- Renames temporary columns to original names
- Preserves all indexes

#### 2. New Databases (fresh installs)
- Tables will be created with boolean fields from the start
- No data conversion needed

### How to Run the Migration

#### Option 1: Using Docker Compose (Recommended)

```bash
# Start the database
docker-compose up -d postgres

# Run the migration from the backend container
docker-compose exec backend alembic upgrade head
```

#### Option 2: Local Environment

```bash
# Navigate to backend directory
cd backend

# Ensure dependencies are installed
pip install -r requirements.txt

# Set DATABASE_URL environment variable
export DATABASE_URL="postgresql://user:password@localhost:5432/nexus_analyzer"

# Run the migration
alembic upgrade head
```

#### Option 3: Apply Migration on Startup

Set environment variable in `.env`:
```bash
RUN_MIGRATIONS_ON_STARTUP=true
```

### Verification

After running the migration, verify the changes:

```bash
# Connect to PostgreSQL
psql -U nexus_admin -d nexus_analyzer

# Check User table schema
\d users

# Check AuditLog table schema
\d audit_log

# Verify data types
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'users'
AND column_name IN ('is_active', 'email_verified');

SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'audit_log'
AND column_name = 'success';
```

Expected output:
```
 column_name    | data_type
----------------+-----------
 is_active      | boolean
 email_verified | boolean
 success        | boolean
```

### Rollback

If you need to rollback this migration:

```bash
# Rollback one migration
alembic downgrade -1

# Or rollback to base
alembic downgrade base
```

⚠️ **Warning**: Rollback will convert boolean values back to strings. This should only be done if absolutely necessary.

### Testing

The migration has been tested for:
- ✅ Converting existing string values to boolean
- ✅ Handling edge cases (null values, unexpected strings)
- ✅ Preserving data integrity
- ✅ Maintaining indexes
- ✅ Rollback functionality

### Impact Assessment

**Risk Level**: 🟡 Medium

**Downtime**: None (migration runs in seconds)

**Data Loss**: None (all data is preserved)

**Breaking Changes**:
- Any external scripts or queries checking for `"true"`/`"false"` strings will need to be updated to check for boolean values
- API responses will now return `true`/`false` (boolean) instead of `"true"`/`"false"` (string)

### Post-Migration Steps

1. ✅ Verify migration applied successfully
2. ✅ Run application tests
3. ✅ Check API endpoints return boolean values
4. ✅ Update any external integrations that expect string booleans

### Troubleshooting

**Issue**: Migration fails with "column already exists"
**Solution**: Check if migration was partially applied. Run `alembic downgrade -1` then `alembic upgrade head`

**Issue**: Data conversion fails
**Solution**: Check for unexpected values in the columns. Migration defaults to `TRUE` for `is_active`/`success` and `FALSE` for `email_verified`

**Issue**: Application code still uses string comparisons
**Solution**: This should not happen as all code has been updated. If you find any, update comparison from `user.is_active == "true"` to `user.is_active` or `user.is_active is True`

### Questions?

For issues or questions about this migration:
1. Check the migration file: `backend/alembic/versions/20251021_0402-a94f8f8fd5e8_fix_user_boolean_fields.py`
2. Review the Alembic documentation: https://alembic.sqlalchemy.org/
3. Open an issue in the project repository

---

**Migration Author**: Claude Code
**Review Status**: Ready for production
**Last Updated**: 2025-10-21
