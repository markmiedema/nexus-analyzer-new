"""Convert string booleans to Boolean type

Revision ID: f517bf0b0366
Revises: 939311a0e4fc
Create Date: 2025-10-21 18:59:03.596940

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f517bf0b0366'
down_revision: Union[str, None] = '939311a0e4fc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Convert users.is_active from string to boolean
    op.execute("""
        UPDATE users 
        SET is_active = CASE 
            WHEN is_active = 'true' THEN TRUE
            WHEN is_active = 'false' THEN FALSE
            ELSE FALSE
        END::text
    """)
    
    op.alter_column('users', 'is_active',
                    type_=sa.Boolean(),
                    postgresql_using='is_active::boolean',
                    nullable=False)
    
    # Convert users.email_verified from string to boolean
    op.execute("""
        UPDATE users 
        SET email_verified = CASE 
            WHEN email_verified = 'true' THEN TRUE
            WHEN email_verified = 'false' THEN FALSE
            ELSE FALSE
        END::text
    """)
    
    op.alter_column('users', 'email_verified',
                    type_=sa.Boolean(),
                    postgresql_using='email_verified::boolean',
                    nullable=False)
    
    # Convert audit_log.success from string to boolean
    op.execute("""
        UPDATE audit_log 
        SET success = CASE 
            WHEN success = 'true' THEN TRUE
            WHEN success = 'false' THEN FALSE
            ELSE TRUE
        END::text
    """)
    
    op.alter_column('audit_log', 'success',
                    type_=sa.Boolean(),
                    postgresql_using='success::boolean',
                    nullable=False)


def downgrade() -> None:
    # Convert back to strings if needed
    op.alter_column('users', 'is_active',
                    type_=sa.String(10),
                    nullable=False)
    
    op.execute("UPDATE users SET is_active = CASE WHEN is_active::boolean THEN 'true' ELSE 'false' END")
    
    op.alter_column('users', 'email_verified',
                    type_=sa.String(10),
                    nullable=False)
    
    op.execute("UPDATE users SET email_verified = CASE WHEN email_verified::boolean THEN 'true' ELSE 'false' END")
    
    op.alter_column('audit_log', 'success',
                    type_=sa.String(10),
                    nullable=False)
    
    op.execute("UPDATE audit_log SET success = CASE WHEN success::boolean THEN 'true' ELSE 'false' END")