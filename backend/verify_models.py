"""
Verification script to check that all models are correctly configured.
Run this to verify models before generating migrations.

Usage:
    python verify_models.py
"""

import sys
from sqlalchemy import inspect
from database import Base, engine
import models

def verify_models():
    """Verify all models are properly configured."""

    print("=" * 60)
    print("Nexus Analyzer - Model Verification")
    print("=" * 60)
    print()

    # Get all tables from metadata
    tables = Base.metadata.tables

    print(f"✓ Found {len(tables)} tables in metadata\n")

    expected_tables = [
        'tenants',
        'users',
        'analyses',
        'business_profiles',
        'physical_locations',
        'transactions',
        'nexus_rules',
        'nexus_results',
        'liability_estimates',
        'state_tax_config',
        'reports',
        'audit_log'
    ]

    print("Checking for expected tables:")
    print("-" * 60)

    all_present = True
    for expected_table in expected_tables:
        if expected_table in tables:
            table = tables[expected_table]
            column_count = len(table.columns)
            fk_count = len([c for c in table.columns if c.foreign_keys])
            index_count = len(table.indexes)

            print(f"✓ {expected_table:30s} | Columns: {column_count:2d} | FKs: {fk_count} | Indexes: {index_count}")
        else:
            print(f"✗ {expected_table:30s} | MISSING!")
            all_present = False

    print()

    if not all_present:
        print("❌ ERROR: Some expected tables are missing!")
        return False

    print("✓ All expected tables are present!")
    print()

    # Check relationships
    print("Checking relationships:")
    print("-" * 60)

    from models import Tenant, User, Analysis, BusinessProfile

    relationships_to_check = [
        ('Tenant', 'users', Tenant),
        ('Tenant', 'analyses', Tenant),
        ('User', 'tenant', User),
        ('User', 'created_analyses', User),
        ('Analysis', 'tenant', Analysis),
        ('Analysis', 'created_by_user', Analysis),
        ('Analysis', 'business_profile', Analysis),
        ('Analysis', 'transactions', Analysis),
        ('BusinessProfile', 'analysis', BusinessProfile),
        ('BusinessProfile', 'physical_locations', BusinessProfile),
    ]

    for model_name, rel_name, model_class in relationships_to_check:
        if hasattr(model_class, rel_name):
            print(f"✓ {model_name}.{rel_name}")
        else:
            print(f"✗ {model_name}.{rel_name} - MISSING!")

    print()

    # Check enums
    print("Checking enums:")
    print("-" * 60)

    from models import (
        TenantStatus, SubscriptionPlan, UserRole, AnalysisStatus,
        LocationType, NexusType, ThresholdMeasurement, MeasurementPeriod,
        NexusDetermination, ConfidenceLevel, RiskLevel, ReportType, ReportStatus
    )

    enums = [
        ('TenantStatus', TenantStatus),
        ('SubscriptionPlan', SubscriptionPlan),
        ('UserRole', UserRole),
        ('AnalysisStatus', AnalysisStatus),
        ('LocationType', LocationType),
        ('NexusType', NexusType),
        ('ThresholdMeasurement', ThresholdMeasurement),
        ('MeasurementPeriod', MeasurementPeriod),
        ('NexusDetermination', NexusDetermination),
        ('ConfidenceLevel', ConfidenceLevel),
        ('RiskLevel', RiskLevel),
        ('ReportType', ReportType),
        ('ReportStatus', ReportStatus),
    ]

    for enum_name, enum_class in enums:
        values = [e.value for e in enum_class]
        print(f"✓ {enum_name:25s} | Values: {len(values)}")

    print()
    print("=" * 60)
    print("✓ Model verification completed successfully!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Ensure Docker services are running: docker-compose up -d postgres")
    print("2. Generate migration: alembic revision --autogenerate -m 'Initial schema'")
    print("3. Review migration file in alembic/versions/")
    print("4. Apply migration: alembic upgrade head")
    print()

    return True


if __name__ == "__main__":
    try:
        success = verify_models()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
