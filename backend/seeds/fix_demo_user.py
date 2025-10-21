"""
Fix demo user password hash.
"""

import sys
sys.path.insert(0, '/app')

from database import SessionLocal
from models.user import User
from models.tenant import Tenant
from services.auth_service import AuthService
import uuid

def fix_demo_user():
    db = SessionLocal()

    try:
        # Delete old demo user
        demo_user = db.query(User).filter(User.email == 'demo@nexusanalyzer.com').first()
        if demo_user:
            db.delete(demo_user)
            db.commit()
            print('✓ Deleted old demo user with corrupted hash')

        # Get demo tenant
        tenant = db.query(Tenant).filter(Tenant.subdomain == 'demo').first()
        if not tenant:
            print('ERROR: Demo tenant not found')
            return

        # Create new demo user with proper hash
        auth_service = AuthService()
        password_hash = auth_service.hash_password('demo123')

        new_user = User(
            user_id=uuid.uuid4(),
            tenant_id=tenant.tenant_id,
            email='demo@nexusanalyzer.com',
            password_hash=password_hash,
            first_name='Demo',
            last_name='User',
            role='admin',
            is_active=True,
            email_verified=True
        )

        db.add(new_user)
        db.commit()

        print('✓ Created demo user with proper password hash')
        print('')
        print('='*50)
        print('DEMO CREDENTIALS:')
        print('='*50)
        print('Email:    demo@nexusanalyzer.com')
        print('Password: demo123')
        print('='*50)
        print('')
        print('Go to http://localhost:3000 and login!')

    except Exception as e:
        print(f'ERROR: {e}')
        db.rollback()
    finally:
        db.close()

if __name__ == '__main__':
    fix_demo_user()
