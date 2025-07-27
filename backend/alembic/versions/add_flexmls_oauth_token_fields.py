"""add flexmls oauth token fields

Revision ID: add_flexmls_oauth_token_fields
Revises: 2ce7c9665fe8
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_flexmls_oauth_token_fields'
down_revision = '2ce7c9665fe8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add FlexMLS OAuth token fields to user table
    op.add_column('user', sa.Column('flexmls_access_token', sa.String(), nullable=True))
    op.add_column('user', sa.Column('flexmls_refresh_token', sa.String(), nullable=True))
    op.add_column('user', sa.Column('flexmls_token_expires_at', sa.String(), nullable=True))


def downgrade() -> None:
    # Remove FlexMLS OAuth token fields from user table
    op.drop_column('user', 'flexmls_access_token')
    op.drop_column('user', 'flexmls_refresh_token')
    op.drop_column('user', 'flexmls_token_expires_at') 