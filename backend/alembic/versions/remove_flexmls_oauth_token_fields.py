"""remove flexmls oauth token fields

Revision ID: remove_flexmls_oauth_token_fields
Revises: add_flexmls_oauth_token_fields
Create Date: 2025-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'remove_oauth_fields'
down_revision = 'add_flexmls_oauth_token_fields'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Remove FlexMLS OAuth token fields from user table
    op.drop_column('user', 'flexmls_access_token')
    op.drop_column('user', 'flexmls_refresh_token')
    op.drop_column('user', 'flexmls_token_expires_at')


def downgrade() -> None:
    # Add back FlexMLS OAuth token fields to user table
    op.add_column('user', sa.Column('flexmls_access_token', sa.String(), nullable=True))
    op.add_column('user', sa.Column('flexmls_refresh_token', sa.String(), nullable=True))
    op.add_column('user', sa.Column('flexmls_token_expires_at', sa.String(), nullable=True)) 