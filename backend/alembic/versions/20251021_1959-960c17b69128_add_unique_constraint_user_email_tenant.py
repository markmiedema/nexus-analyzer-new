"""Add unique constraint on user email per tenant

Revision ID: 960c17b69128
Revises: f517bf0b0366
Create Date: 2025-10-21 19:59:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '960c17b69128'
down_revision: Union[str, None] = 'f517bf0b0366'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add unique constraint to ensure one email per tenant."""
    # Create unique constraint on (email, tenant_id)
    op.create_unique_constraint(
        'uq_user_email_tenant',  # constraint name
        'users',  # table name
        ['email', 'tenant_id']  # columns
    )


def downgrade() -> None:
    """Remove unique constraint."""
    op.drop_constraint('uq_user_email_tenant', 'users', type_='unique')
