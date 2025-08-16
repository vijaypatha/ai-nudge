"""merge survey migration

Revision ID: 015cefa1a6b3
Revises: add_client_intake_survey_table, cbe7cd5783fa
Create Date: 2025-08-11 17:45:19.947616

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '015cefa1a6b3'
down_revision: Union[str, Sequence[str], None] = ('add_client_intake_survey_table', 'cbe7cd5783fa')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
