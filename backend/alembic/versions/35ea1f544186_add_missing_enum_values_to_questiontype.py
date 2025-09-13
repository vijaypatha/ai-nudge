"""add_missing_enum_values_to_questiontype

Revision ID: 35ea1f544186
Revises: 8027110b2edf
Create Date: 2025-09-13 07:33:18.544281

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '35ea1f544186'
down_revision: Union[str, Sequence[str], None] = '8027110b2edf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Drop and recreate enum with correct values
    op.execute("ALTER TABLE surveyquestion ALTER COLUMN question_type TYPE varchar(50)")
    op.execute("DROP TYPE questiontype")
    op.execute("CREATE TYPE questiontype AS ENUM ('text', 'number', 'select', 'multi_select', 'range', 'boolean')")
    op.execute("ALTER TABLE surveyquestion ALTER COLUMN question_type TYPE questiontype USING question_type::questiontype")

def downgrade() -> None:
    """Downgrade schema."""
    # Recreate old enum
    op.execute("ALTER TABLE surveyquestion ALTER COLUMN question_type TYPE varchar(50)")
    op.execute("DROP TYPE questiontype")
    op.execute("CREATE TYPE questiontype AS ENUM ('TEXT', 'TEXTAREA', 'MULTIPLE_CHOICE', 'CHECKBOXES', 'SCALE')")
    op.execute("ALTER TABLE surveyquestion ALTER COLUMN question_type TYPE questiontype USING question_type::questiontype")

