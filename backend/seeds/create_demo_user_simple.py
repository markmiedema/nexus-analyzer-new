"""
Create demo user using direct SQL to bypass bcrypt compatibility issues.
"""

import psycopg2
from psycopg2 import sql
import uuid
import os

# Get database connection details from environment
DB_USER = os.getenv('POSTGRES_USER', 'nexus_admin')
DB_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'nexus_password')
DB_NAME = os.getenv('POSTGRES_DB', 'nexus_analyzer')
DB_HOST = 'postgres'
DB_PORT = '5432'

def create_demo_data():
    try:
        # Connect to database
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        cur = conn.cursor()

        # Check if demo tenant exists
        cur.execute("SELECT tenant_id, company_name FROM tenants WHERE subdomain = 'demo'")
        tenant = cur.fetchone()

        if not tenant:
            # Create tenant
            tenant_id = str(uuid.uuid4())
            cur.execute(
                "INSERT INTO tenants (tenant_id, company_name, subdomain, is_active) VALUES (%s, %s, %s, %s)",
                (tenant_id, 'Demo Company', 'demo', 'true')
            )
            conn.commit()
            print(f"✓ Created tenant: Demo Company")
        else:
            tenant_id = str(tenant[0])
            print(f"Demo tenant already exists: {tenant[1]}")

        # Delete existing demo user if exists
        cur.execute("DELETE FROM users WHERE email = 'demo@nexusanalyzer.com'")
        if cur.rowcount > 0:
            print("Deleted existing demo user")
        conn.commit()

        # Create new demo user
        # Pre-hashed password for 'demo123' using bcrypt
        # Generated with: python -c "from passlib.hash import bcrypt; print(bcrypt.hash('demo123'))"
        # This is a valid bcrypt hash for the password 'demo123'
        password_hash = '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqgOqF3oCO'

        user_id = str(uuid.uuid4())
        cur.execute(
            """
            INSERT INTO users (
                user_id, tenant_id, email, password_hash,
                first_name, last_name, role, is_active, email_verified, created_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW()
            )
            """,
            (
                user_id, tenant_id, 'demo@nexusanalyzer.com', password_hash,
                'Demo', 'User', 'admin', 'true', 'true'
            )
        )
        conn.commit()

        print(f"✓ Created user: demo@nexusanalyzer.com")
        print("\n" + "="*50)
        print("DEMO CREDENTIALS:")
        print("="*50)
        print(f"Email:    demo@nexusanalyzer.com")
        print(f"Password: demo123")
        print(f"Role:     admin")
        print("="*50)

        cur.close()
        conn.close()

    except Exception as e:
        print(f"Error creating demo data: {e}")
        raise

if __name__ == '__main__':
    create_demo_data()
