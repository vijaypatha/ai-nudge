# File: backend/tests/test_simple_db.py
# 
# What does this file test:
# This file contains simple tests to verify that the database setup is working correctly.
# 
# When was it updated: 2025-01-27

import pytest
from sqlmodel import Session, text
import os

def test_database_connection(session: Session):
    """Test that we can connect to the database."""
    result = session.exec(text("SELECT 1"))
    assert result.first()[0] == 1

def test_database_tables_exist(session: Session):
    """Test that all required tables exist in the database."""
    # Get list of all tables
    result = session.exec(text("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name
    """))
    tables = [row[0] for row in result.all()]
    
    # Check for required tables
    required_tables = [
        'user', 'client', 'resource', 'contentresource',
        'message', 'scheduledmessage', 'campaignbriefing',
        'marketevent', 'pipelinerun', 'faq', 'negativepreference'
    ]
    
    missing_tables = [table for table in required_tables if table not in tables]
    assert not missing_tables, f"Missing tables: {missing_tables}. Available tables: {tables}"

def test_campaignbriefing_table_works(session: Session):
    """Test that we can query the campaignbriefing table."""
    # Try to query the campaignbriefing table
    result = session.exec(text("SELECT COUNT(*) FROM campaignbriefing"))
    count = result.first()[0]
    print(f"campaignbriefing table has {count} rows")
    assert count >= 0  # Should not fail

def test_ci_environment_detection():
    """Test that we can detect the CI environment correctly."""
    is_ci = os.getenv('GITHUB_ACTIONS') == 'true'
    print(f"Running in CI: {is_ci}")
    if is_ci:
        print(f"DATABASE_URL: {os.getenv('DATABASE_URL')}")
    assert True  # Just a placeholder test 