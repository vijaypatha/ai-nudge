"""merge heads migration

Revision ID: merge_heads_migration
Revises: add_negativepreference_table, remove_oauth_fields
Create Date: 2025-07-27 01:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'merge_heads_migration'
down_revision: Union[str, Sequence[str], None] = ('add_negativepreference_table', 'remove_oauth_fields')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # This is a merge migration - no schema changes needed
    pass


def downgrade() -> None:
    """Downgrade schema."""
    # This is a merge migration - no schema changes needed
    pass 