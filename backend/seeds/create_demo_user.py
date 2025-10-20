"""
Create demo tenant and user for development/testing.
"""

from database import SessionLocal
from models.tenant import Tenant
from models.user import User, UserRole
from auth_utils import get_password_hash
import uuid

def create_demo_data():
    db = SessionLocal()

    try:
        # Check if demo tenant already exists
        existing_tenant = db.query(Tenant).filter(Tenant.subdomain == 'demo').first()

        if existing_tenant:
            print("Demo tenant already exists!")
            print(f"Tenant: {existing_tenant.company_name}")

            # Check for demo user
            existing_user = db.query(User).filter(User.email == 'demo@nexusanalyzer.com').first()
            if existing_user:
                print(f"Demo user already exists: demo@nexusanalyzer.com")
                return

        # Create tenant
        if not existing_tenant:
            tenant = Tenant(
                tenant_id=str(uuid.uuid4()),
                company_name='Demo Company',
                subdomain='demo',
                is_active=True
            )
            db.add(tenant)
            db.commit()
            db.refresh(tenant)
            print(f"✓ Created tenant: {tenant.company_name}")
        else:
            tenant = existing_tenant

        # Create demo user
        user = User(
            user_id=str(uuid.uuid4()),
            tenant_id=tenant.tenant_id,
            email='demo@nexusanalyzer.com',
            full_name='Demo User',
            hashed_password=get_password_hash('demo123'),
            role=UserRole.ADMIN,
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        print(f"✓ Created user: {user.email}")
        print("\n" + "="*50)
        print("DEMO CREDENTIALS:")
        print("="*50)
        print(f"Email:    demo@nexusanalyzer.com")
        print(f"Password: demo123")
        print(f"Role:     {user.role.value}")
        print("="*50)

    except Exception as e:
        print(f"Error creating demo data: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == '__main__':
    create_demo_data()
