"""
Verify demo user exists and has correct boolean field values.
"""

from database import SessionLocal
from models.user import User
from models.tenant import Tenant

def verify_demo_user():
    db = SessionLocal()

    try:
        # Find demo user
        user = db.query(User).filter(User.email == 'demo@nexusanalyzer.com').first()

        if not user:
            print("❌ Demo user not found!")
            print("\nRun: python backend/seeds/create_demo_user.py")
            return

        # Get tenant info
        tenant = db.query(Tenant).filter(Tenant.tenant_id == user.tenant_id).first()

        print("="*60)
        print("DEMO USER VERIFICATION")
        print("="*60)
        print(f"✓ User found: {user.email}")
        print(f"✓ Tenant: {tenant.subdomain if tenant else 'NOT FOUND'}")
        print(f"  - Company: {tenant.company_name if tenant else 'N/A'}")
        print(f"\nUser Details:")
        print(f"  - User ID: {user.user_id}")
        print(f"  - Name: {user.first_name} {user.last_name}")
        print(f"  - Role: {user.role.value}")
        print(f"  - is_active: {user.is_active} (type: {type(user.is_active).__name__})")
        print(f"  - email_verified: {user.email_verified} (type: {type(user.email_verified).__name__})")
        print(f"  - Has password: {'Yes' if user.password_hash else 'No'}")

        # Check if boolean types are correct
        if isinstance(user.is_active, bool) and isinstance(user.email_verified, bool):
            print("\n✓ Boolean fields have correct types!")
        else:
            print("\n❌ WARNING: Boolean fields are not proper booleans!")
            print(f"   is_active is {type(user.is_active).__name__}, should be bool")
            print(f"   email_verified is {type(user.email_verified).__name__}, should be bool")

        # Check values
        if user.is_active and user.email_verified:
            print("✓ User is active and email is verified")
        else:
            if not user.is_active:
                print("❌ WARNING: User is NOT active!")
            if not user.email_verified:
                print("⚠️  Email is not verified (this is OK for login)")

        print("\n" + "="*60)
        print("LOGIN CREDENTIALS:")
        print("="*60)
        print(f"URL:      http://localhost:3000")
        print(f"Tenant:   demo")
        print(f"Email:    demo@nexusanalyzer.com")
        print(f"Password: demo123")
        print("="*60)

    except Exception as e:
        print(f"❌ Error verifying demo user: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == '__main__':
    verify_demo_user()
