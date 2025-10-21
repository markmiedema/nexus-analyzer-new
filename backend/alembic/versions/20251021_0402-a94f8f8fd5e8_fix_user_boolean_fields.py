"""fix_user_boolean_fields

Revision ID: a94f8f8fd5e8
Revises:
Create Date: 2025-10-21 04:02:34.652157

This migration converts boolean fields from String(10) to proper Boolean types.

Models affected:
- User: is_active, email_verified
- AuditLog: success

For existing databases:
- Converts "true" strings to TRUE boolean
- Converts "false" strings to FALSE boolean

For new databases:
- Creates tables with Boolean fields from the start
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'a94f8f8fd5e8'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Convert boolean fields from VARCHAR(10) to BOOLEAN.

    This handles both:
    1. Existing databases with String(10) fields - converts data and alters columns
    2. New databases - the model will create tables with Boolean from the start
    """
    # Bind to the connection to check if table exists
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # =========================================================================
    # Convert User table boolean fields
    # =========================================================================
    if 'users' in inspector.get_table_names():
        # Table exists - need to convert columns

        # Step 1: Add temporary boolean columns
        op.add_column('users', sa.Column('is_active_new', sa.Boolean(), nullable=True))
        op.add_column('users', sa.Column('email_verified_new', sa.Boolean(), nullable=True))

        # Step 2: Migrate data from string to boolean
        # Convert "true" -> TRUE, "false" -> FALSE, handle any edge cases
        op.execute("""
            UPDATE users
            SET is_active_new = CASE
                WHEN LOWER(is_active) = 'true' THEN TRUE
                WHEN LOWER(is_active) = 'false' THEN FALSE
                ELSE TRUE  -- Default to true for safety
            END
        """)

        op.execute("""
            UPDATE users
            SET email_verified_new = CASE
                WHEN LOWER(email_verified) = 'true' THEN TRUE
                WHEN LOWER(email_verified) = 'false' THEN FALSE
                ELSE FALSE  -- Default to false for safety
            END
        """)

        # Step 3: Make new columns non-nullable
        op.alter_column('users', 'is_active_new', nullable=False)
        op.alter_column('users', 'email_verified_new', nullable=False)

        # Step 4: Drop old columns
        op.drop_column('users', 'is_active')
        op.drop_column('users', 'email_verified')

        # Step 5: Rename new columns to original names
        op.alter_column('users', 'is_active_new', new_column_name='is_active')
        op.alter_column('users', 'email_verified_new', new_column_name='email_verified')

        print("✓ Successfully converted User.is_active and User.email_verified to Boolean type")
    else:
        # Table doesn't exist - it will be created by the model with Boolean fields
        print("✓ Users table doesn't exist yet - will be created with Boolean fields")

    # =========================================================================
    # Convert AuditLog table boolean field
    # =========================================================================
    if 'audit_log' in inspector.get_table_names():
        # Table exists - need to convert column

        # Step 1: Add temporary boolean column
        op.add_column('audit_log', sa.Column('success_new', sa.Boolean(), nullable=True))

        # Step 2: Migrate data from string to boolean
        op.execute("""
            UPDATE audit_log
            SET success_new = CASE
                WHEN LOWER(success) = 'true' THEN TRUE
                WHEN LOWER(success) = 'false' THEN FALSE
                ELSE TRUE  -- Default to true for safety
            END
        """)

        # Step 3: Make new column non-nullable
        op.alter_column('audit_log', 'success_new', nullable=False)

        # Step 4: Drop old column (including its index)
        op.drop_index('ix_audit_log_success', table_name='audit_log')
        op.drop_column('audit_log', 'success')

        # Step 5: Rename new column to original name
        op.alter_column('audit_log', 'success_new', new_column_name='success')

        # Step 6: Recreate the index
        op.create_index('ix_audit_log_success', 'audit_log', ['success'])

        print("✓ Successfully converted AuditLog.success to Boolean type")
    else:
        # Table doesn't exist - it will be created by the model with Boolean fields
        print("✓ AuditLog table doesn't exist yet - will be created with Boolean fields")


def downgrade() -> None:
    """
    Revert boolean fields from BOOLEAN to VARCHAR(10).

    This is provided for rollback purposes but should rarely be needed.
    """
    # Bind to the connection to check if table exists
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # =========================================================================
    # Revert AuditLog table boolean field
    # =========================================================================
    if 'audit_log' in inspector.get_table_names():
        # Step 1: Add temporary string column
        op.add_column('audit_log', sa.Column('success_new', sa.String(10), nullable=True))

        # Step 2: Migrate data from boolean to string
        op.execute("""
            UPDATE audit_log
            SET success_new = CASE
                WHEN success = TRUE THEN 'true'
                WHEN success = FALSE THEN 'false'
                ELSE 'true'
            END
        """)

        # Step 3: Make new column non-nullable
        op.alter_column('audit_log', 'success_new', nullable=False)

        # Step 4: Drop old column (including its index)
        op.drop_index('ix_audit_log_success', table_name='audit_log')
        op.drop_column('audit_log', 'success')

        # Step 5: Rename new column to original name
        op.alter_column('audit_log', 'success_new', new_column_name='success')

        # Step 6: Recreate the index
        op.create_index('ix_audit_log_success', 'audit_log', ['success'])

        print("✓ Reverted AuditLog.success to String(10) type")

    # =========================================================================
    # Revert User table boolean fields
    # =========================================================================
    if 'users' in inspector.get_table_names():
        # Step 1: Add temporary string columns
        op.add_column('users', sa.Column('is_active_new', sa.String(10), nullable=True))
        op.add_column('users', sa.Column('email_verified_new', sa.String(10), nullable=True))

        # Step 2: Migrate data from boolean to string
        op.execute("""
            UPDATE users
            SET is_active_new = CASE
                WHEN is_active = TRUE THEN 'true'
                WHEN is_active = FALSE THEN 'false'
                ELSE 'true'
            END
        """)

        op.execute("""
            UPDATE users
            SET email_verified_new = CASE
                WHEN email_verified = TRUE THEN 'true'
                WHEN email_verified = FALSE THEN 'false'
                ELSE 'false'
            END
        """)

        # Step 3: Make new columns non-nullable
        op.alter_column('users', 'is_active_new', nullable=False)
        op.alter_column('users', 'email_verified_new', nullable=False)

        # Step 4: Drop old columns
        op.drop_column('users', 'is_active')
        op.drop_column('users', 'email_verified')

        # Step 5: Rename new columns to original names
        op.alter_column('users', 'is_active_new', new_column_name='is_active')
        op.alter_column('users', 'email_verified_new', new_column_name='email_verified')

        print("✓ Reverted User.is_active and User.email_verified to String(10) type")
