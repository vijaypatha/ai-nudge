"""add_client_intake_survey_table

Revision ID: add_client_intake_survey_table
Revises: 2ce7c9665fe8
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_client_intake_survey_table'
down_revision = '2ce7c9665fe8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add survey-related fields to client table
    op.add_column('client', sa.Column('intake_survey_completed', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('client', sa.Column('intake_survey_sent_at', sa.String(), nullable=True))
    op.create_index(op.f('ix_client_intake_survey_completed'), 'client', ['intake_survey_completed'], unique=False)

    # Add survey configuration fields to user table
    op.add_column('user', sa.Column('intake_survey_enabled', sa.Boolean(), nullable=False, server_default='true'))
    op.add_column('user', sa.Column('intake_survey_auto_send', sa.Boolean(), nullable=False, server_default='true'))
    op.add_column('user', sa.Column('intake_survey_delay_hours', sa.Integer(), nullable=False, server_default='24'))

    # Create clientintakesurvey table
    op.create_table('clientintakesurvey',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('client_id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('survey_type', sa.String(), nullable=False),
        sa.Column('survey_version', sa.String(), nullable=False, server_default='1.0'),
        sa.Column('completed_at', sa.String(), nullable=True),
        sa.Column('responses', sa.JSON(), nullable=True),
        sa.Column('processed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('preferences_extracted', sa.JSON(), nullable=True),
        sa.Column('tags_generated', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['client_id'], ['client.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_clientintakesurvey_client_id'), 'clientintakesurvey', ['client_id'], unique=False)
    op.create_index(op.f('ix_clientintakesurvey_user_id'), 'clientintakesurvey', ['user_id'], unique=False)
    op.create_index(op.f('ix_clientintakesurvey_survey_type'), 'clientintakesurvey', ['survey_type'], unique=False)
    op.create_index(op.f('ix_clientintakesurvey_processed'), 'clientintakesurvey', ['processed'], unique=False)


def downgrade() -> None:
    # Drop clientintakesurvey table
    op.drop_index(op.f('ix_clientintakesurvey_processed'), table_name='clientintakesurvey')
    op.drop_index(op.f('ix_clientintakesurvey_survey_type'), table_name='clientintakesurvey')
    op.drop_index(op.f('ix_clientintakesurvey_user_id'), table_name='clientintakesurvey')
    op.drop_index(op.f('ix_clientintakesurvey_client_id'), table_name='clientintakesurvey')
    op.drop_table('clientintakesurvey')

    # Drop survey configuration fields from user table
    op.drop_column('user', 'intake_survey_delay_hours')
    op.drop_column('user', 'intake_survey_auto_send')
    op.drop_column('user', 'intake_survey_enabled')

    # Drop survey-related fields from client table
    op.drop_index(op.f('ix_client_intake_survey_completed'), table_name='client')
    op.drop_column('client', 'intake_survey_sent_at')
    op.drop_column('client', 'intake_survey_completed')
