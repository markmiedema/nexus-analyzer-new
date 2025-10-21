"""
Test script to verify unique constraint on user email per tenant.
"""

from database import SessionLocal
from models.user import User, UserRole
from models.tenant import Tenant
from services.auth_service import AuthService
import uuid

def test_unique_constraint():
    db = SessionLocal()

    try:
        # Get or create test tenant
        test_tenant = db.query(Tenant).filter(Tenant.subdomain == 'test-unique').first()
        if not test_tenant:
            test_tenant = Tenant(
                tenant_id=str(uuid.uuid4()),
                company_name='Test Unique Company',
                subdomain='test-unique',
                is_active=True
            )
            db.add(test_tenant)
            db.commit()
            db.refresh(test_tenant)
            print(f"✓ Created test tenant: {test_tenant.subdomain}")
        else:
            print(f"✓ Using existing test tenant: {test_tenant.subdomain}")

        # Get or create second test tenant
        test_tenant2 = db.query(Tenant).filter(Tenant.subdomain == 'test-unique2').first()
        if not test_tenant2:
            test_tenant2 = Tenant(
                tenant_id=str(uuid.uuid4()),
                company_name='Test Unique Company 2',
                subdomain='test-unique2',
                is_active=True
            )
            db.add(test_tenant2)
            db.commit()
            db.refresh(test_tenant2)
            print(f"✓ Created second test tenant: {test_tenant2.subdomain}")
        else:
            print(f"✓ Using existing second test tenant: {test_tenant2.subdomain}")

        # Clean up any existing test users
        db.query(User).filter(User.email == 'test@unique.com').delete()
        db.commit()
        print("✓ Cleaned up existing test users")

        # TEST 1: Create first user
        print("\n" + "="*60)
        print("TEST 1: Creating first user with test@unique.com in tenant 1")
        print("="*60)
        user1 = User(
            user_id=str(uuid.uuid4()),
            tenant_id=test_tenant.tenant_id,
            email='test@unique.com',
            first_name='Test',
            last_name='User1',
            password_hash=AuthService.hash_password('test123'),
            role=UserRole.VIEWER,
            is_active=True,
            email_verified=True
        )
        db.add(user1)
        db.commit()
        print("✓ SUCCESS: First user created successfully")

        # TEST 2: Try to create duplicate user in SAME tenant (should fail)
        print("\n" + "="*60)
        print("TEST 2: Attempting to create duplicate email in SAME tenant")
        print("        (This should FAIL with unique constraint violation)")
        print("="*60)
        try:
            user2 = User(
                user_id=str(uuid.uuid4()),
                tenant_id=test_tenant.tenant_id,  # Same tenant
                email='test@unique.com',  # Same email
                first_name='Test',
                last_name='User2',
                password_hash=AuthService.hash_password('test123'),
                role=UserRole.VIEWER,
                is_active=True,
                email_verified=True
            )
            db.add(user2)
            db.commit()
            print("❌ FAILED: Duplicate user was created (unique constraint NOT working!)")
            return False
        except Exception as e:
            db.rollback()
            if 'uq_user_email_tenant' in str(e) or 'unique constraint' in str(e).lower():
                print(f"✓ SUCCESS: Unique constraint prevented duplicate")
                print(f"   Error: {str(e)[:100]}...")
            else:
                print(f"❌ FAILED: Got unexpected error: {e}")
                return False

        # TEST 3: Create same email in DIFFERENT tenant (should succeed)
        print("\n" + "="*60)
        print("TEST 3: Creating same email in DIFFERENT tenant")
        print("        (This should SUCCEED - allows multi-tenant)")
        print("="*60)
        try:
            user3 = User(
                user_id=str(uuid.uuid4()),
                tenant_id=test_tenant2.tenant_id,  # Different tenant
                email='test@unique.com',  # Same email
                first_name='Test',
                last_name='User3',
                password_hash=AuthService.hash_password('test123'),
                role=UserRole.VIEWER,
                is_active=True,
                email_verified=True
            )
            db.add(user3)
            db.commit()
            print("✓ SUCCESS: Same email allowed in different tenant (multi-tenant working!)")
        except Exception as e:
            db.rollback()
            print(f"❌ FAILED: Could not create user in different tenant: {e}")
            return False

        # Verify both users exist
        users = db.query(User).filter(User.email == 'test@unique.com').all()
        print(f"\n✓ Total users with test@unique.com: {len(users)}")
        for user in users:
            tenant = db.query(Tenant).filter(Tenant.tenant_id == user.tenant_id).first()
            print(f"   - {user.email} in tenant '{tenant.subdomain}'")

        print("\n" + "="*60)
        print("ALL TESTS PASSED!")
        print("="*60)
        print("✓ Unique constraint is working correctly")
        print("✓ Same email blocked within same tenant")
        print("✓ Same email allowed across different tenants")
        print("="*60)

        return True

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False
    finally:
        # Clean up test data
        try:
            db.query(User).filter(User.email == 'test@unique.com').delete()
            db.commit()
            print("\n✓ Cleaned up test users")
        except:
            pass
        db.close()

if __name__ == '__main__':
    success = test_unique_constraint()
    exit(0 if success else 1)
