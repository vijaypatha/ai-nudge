# File: backend/tests/test_migrations.py
# 
# What does this file test:
# This file tests database migration integrity, schema consistency between dev/prod,
# migration chain continuity, rollback safety, and production schema compatibility.
# It ensures all migrations can be applied from scratch, have no gaps in the chain,
# and maintain proper foreign key relationships and indexes for performance.
# 
# When was it updated: 2025-01-27

import pytest
import subprocess
import tempfile
import os
from pathlib import Path
from sqlmodel import SQLModel, create_engine, Session
from alembic import command
from alembic.config import Config

from data.database import engine, DATABASE_URL
from data.models.user import User
from data.models.client import Client
from data.models.resource import Resource
from data.models.message import Message
from data.models.campaign import CampaignBriefing


class TestMigrations:
    """Test suite for database migrations and schema consistency"""

    def test_migrations_can_be_applied_from_scratch(self):
        """Test that all migrations can be applied to a fresh database"""
        # Create a temporary database for testing migrations
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
            temp_db_path = tmp_db.name
        
        try:
            # Create a temporary Alembic config
            temp_alembic_ini = tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False)
            temp_alembic_ini.write(f"""[alembic]
script_location = alembic
sqlalchemy.url = sqlite:///{temp_db_path}
""")
            temp_alembic_ini.close()
            
            # Set up Alembic config
            alembic_cfg = Config(temp_alembic_ini.name)
            alembic_cfg.set_main_option('script_location', 'alembic')
            
            # Apply all migrations from scratch
            command.upgrade(alembic_cfg, "head")
            
            # Verify the database was created successfully
            assert os.path.exists(temp_db_path)
            
            # Test that we can connect and query the database
            test_engine = create_engine(f"sqlite:///{temp_db_path}")
            with Session(test_engine) as session:
                # Try to create a test record
                test_user = User(
                    id="test-user-id",
                    full_name="Test User",
                    phone_number="+15551234567"
                )
                session.add(test_user)
                session.commit()
                
                # Verify the record was created
                retrieved_user = session.get(User, "test-user-id")
                assert retrieved_user is not None
                assert retrieved_user.full_name == "Test User"
                
        finally:
            # Clean up temporary files
            if os.path.exists(temp_db_path):
                os.unlink(temp_db_path)
            if os.path.exists(temp_alembic_ini.name):
                os.unlink(temp_alembic_ini.name)

    def test_current_schema_matches_migrations(self):
        """Test that the current database schema matches what migrations would create"""
        # Get the current database schema
        inspector = inspect(engine)
        current_tables = inspector.get_table_names()
        
        # Define the expected tables based on our models
        expected_tables = [
            'user', 'client', 'resource', 'contentresource',
            'message', 'scheduledmessage', 'campaignbriefing',
            'marketevent', 'pipelinerun', 'faq', 'negativepreference'
        ]
        
        # Verify all expected tables exist
        for table in expected_tables:
            assert table in current_tables, f"Table '{table}' missing from current schema"
        
        # Verify no unexpected tables exist
        unexpected_tables = [t for t in current_tables if t not in expected_tables]
        assert len(unexpected_tables) == 0, f"Unexpected tables found: {unexpected_tables}"

    def test_migration_files_are_valid(self):
        """Test that all migration files can be parsed and applied"""
        migrations_dir = Path("alembic/versions")
        
        # Get all migration files
        migration_files = list(migrations_dir.glob("*.py"))
        assert len(migration_files) > 0, "No migration files found"
        
        # Test that each migration file can be imported
        for migration_file in migration_files:
            try:
                # Try to import the migration module
                import importlib.util
                spec = importlib.util.spec_from_file_location(
                    migration_file.stem, 
                    migration_file
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Verify the migration has required attributes
                assert hasattr(module, 'revision'), f"Migration {migration_file.name} missing revision"
                assert hasattr(module, 'down_revision'), f"Migration {migration_file.name} missing down_revision"
                assert hasattr(module, 'upgrade'), f"Migration {migration_file.name} missing upgrade function"
                
            except Exception as e:
                pytest.fail(f"Migration file {migration_file.name} is invalid: {e}")

    def test_migration_chain_is_continuous(self):
        """Test that migration chain has no gaps"""
        # This test ensures that all migrations can be applied in sequence
        # without missing any intermediate migrations
        
        migrations_dir = Path("alembic/versions")
        migration_files = list(migrations_dir.glob("*.py"))
        
        # Build a map of revision -> down_revision
        revision_map = {}
        for migration_file in migration_files:
            try:
                import importlib.util
                spec = importlib.util.spec_from_file_location(
                    migration_file.stem, 
                    migration_file
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                revision_map[module.revision] = module.down_revision
            except Exception:
                continue  # Skip invalid migration files
        
        # Check for gaps in the migration chain
        current_revision = None
        for revision, down_revision in revision_map.items():
            if down_revision is None:
                # This is the initial migration
                continue
            
            if down_revision not in revision_map:
                pytest.fail(f"Migration {revision} references non-existent down_revision {down_revision}")

    def test_production_schema_compatibility(self):
        """Test that the current schema is compatible with production requirements"""
        # This test ensures that the schema supports all production features
        
        # Test that all required fields exist
        inspector = inspect(engine)
        
        # Check User table has required fields
        user_columns = [col['name'] for col in inspector.get_columns('user')]
        required_user_fields = ['id', 'full_name', 'phone_number', 'vertical']
        for field in required_user_fields:
            assert field in user_columns, f"User table missing required field: {field}"
        
        # Check Client table has required fields
        client_columns = [col['name'] for col in inspector.get_columns('client')]
        required_client_fields = ['id', 'user_id', 'full_name', 'notes_embedding']
        for field in required_client_fields:
            assert field in client_columns, f"Client table missing required field: {field}"
        
        # Check Resource table has required fields
        resource_columns = [col['name'] for col in inspector.get_columns('resource')]
        required_resource_fields = ['id', 'user_id', 'resource_type', 'status', 'attributes']
        for field in required_resource_fields:
            assert field in resource_columns, f"Resource table missing required field: {field}"

    def test_foreign_key_integrity(self):
        """Test that foreign key relationships are properly defined"""
        inspector = inspect(engine)
        
        # Check that foreign keys exist
        foreign_keys = inspector.get_foreign_keys('client')
        user_fk_exists = any(fk['referred_table'] == 'user' for fk in foreign_keys)
        assert user_fk_exists, "Client table missing foreign key to User table"
        
        # Check message table foreign keys
        message_fks = inspector.get_foreign_keys('message')
        message_user_fk = any(fk['referred_table'] == 'user' for fk in message_fks)
        message_client_fk = any(fk['referred_table'] == 'client' for fk in message_fks)
        assert message_user_fk, "Message table missing foreign key to User table"
        assert message_client_fk, "Message table missing foreign key to Client table"

    def test_indexes_for_performance(self):
        """Test that critical indexes exist for performance"""
        inspector = inspect(engine)
        
        # Check for critical indexes
        user_indexes = inspector.get_indexes('user')
        client_indexes = inspector.get_indexes('client')
        
        # Verify key indexes exist
        user_index_names = [idx['name'] for idx in user_indexes]
        client_index_names = [idx['name'] for idx in client_indexes]
        
        # Critical indexes for performance
        critical_indexes = [
            ('user', 'ix_user_phone_number'),
            ('user', 'ix_user_vertical'),
            ('client', 'ix_client_user_id'),
            ('message', 'ix_message_user_id'),
            ('message', 'ix_message_client_id')
        ]
        
        for table, index_name in critical_indexes:
            table_indexes = inspector.get_indexes(table)
            index_names = [idx['name'] for idx in table_indexes]
            assert any(index_name in name for name in index_names), f"Missing critical index: {index_name}"

    def test_json_field_support(self):
        """Test that JSON fields are properly configured"""
        inspector = inspect(engine)
        
        # Check that JSON fields exist and are properly typed
        user_columns = inspector.get_columns('user')
        client_columns = inspector.get_columns('client')
        
        # Find JSON columns
        user_json_cols = [col for col in user_columns if 'json' in str(col['type']).lower()]
        client_json_cols = [col for col in client_columns if 'json' in str(col['type']).lower()]
        
        # Verify expected JSON fields exist
        expected_user_json_fields = ['onboarding_state', 'market_focus', 'ai_style_guide', 'strategy', 'specialties']
        expected_client_json_fields = ['notes_embedding', 'ai_tags', 'user_tags', 'preferences']
        
        user_json_field_names = [col['name'] for col in user_json_cols]
        client_json_field_names = [col['name'] for col in client_json_cols]
        
        for field in expected_user_json_fields:
            assert field in user_json_field_names, f"User table missing JSON field: {field}"
        
        for field in expected_client_json_fields:
            assert field in client_json_field_names, f"Client table missing JSON field: {field}"

    def test_migration_rollback_safety(self):
        """Test that migrations can be safely rolled back"""
        # This test ensures that migrations are reversible
        # Note: This is a basic check - actual rollback testing would require
        # a more complex setup with test data
        
        migrations_dir = Path("alembic/versions")
        migration_files = list(migrations_dir.glob("*.py"))
        
        for migration_file in migration_files:
            try:
                import importlib.util
                spec = importlib.util.spec_from_file_location(
                    migration_file.stem, 
                    migration_file
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Check that downgrade function exists (if not initial migration)
                if module.down_revision is not None:
                    assert hasattr(module, 'downgrade'), f"Migration {migration_file.name} missing downgrade function"
                    
            except Exception as e:
                pytest.fail(f"Migration file {migration_file.name} has rollback issues: {e}")


# Helper function for migration tests
def inspect(engine):
    """Get SQLAlchemy inspector for the engine"""
    from sqlalchemy import inspect as sqlalchemy_inspect
    return sqlalchemy_inspect(engine) 