# File: backend/tests/test_database_schema.py
# 
# What does this file test:
# This file tests that the database schema is properly set up and all required tables exist.
# This is critical for CI environments where the database needs to be initialized from scratch.
# 
# When was it updated: 2025-01-27

import pytest
from sqlmodel import Session, select, text
from data.models import (
    User, Client, Resource, ContentResource, Message, ScheduledMessage,
    CampaignBriefing, MarketEvent, PipelineRun, Faq, NegativePreference
)

def test_database_tables_exist(session: Session):
    """Test that all required database tables exist."""
    # Test that we can query the user table
    result = session.exec(select(User)).all()
    assert isinstance(result, list)
    
    # Test that we can query the client table
    result = session.exec(select(Client)).all()
    assert isinstance(result, list)
    
    # Test that we can query the campaignbriefing table
    result = session.exec(select(CampaignBriefing)).all()
    assert isinstance(result, list)
    
    # Test that we can query the resource table
    result = session.exec(select(Resource)).all()
    assert isinstance(result, list)
    
    # Test that we can query the message table
    result = session.exec(select(Message)).all()
    assert isinstance(result, list)
    
    # Test that we can query the scheduledmessage table
    result = session.exec(select(ScheduledMessage)).all()
    assert isinstance(result, list)

def test_campaignbriefing_table_structure(session: Session):
    """Test that the campaignbriefing table has the expected structure."""
    # Try to insert a minimal campaign briefing to test the table structure
    from data.models.campaign import CampaignStatus
    from uuid import uuid4
    
    test_briefing = CampaignBriefing(
        id=uuid4(),
        user_id=uuid4(),
        headline="Test Headline",
        campaign_type="test",
        key_intel={},
        original_draft="Test draft",
        status=CampaignStatus.DRAFT
    )
    
    session.add(test_briefing)
    session.commit()
    session.refresh(test_briefing)
    
    # Verify we can retrieve it
    retrieved = session.get(CampaignBriefing, test_briefing.id)
    assert retrieved is not None
    assert retrieved.headline == "Test Headline"
    assert retrieved.campaign_type == "test"
    
    # Clean up
    session.delete(test_briefing)
    session.commit()

def test_database_connection_info(session: Session):
    """Test to log database connection information for debugging."""
    # Get database info
    result = session.exec(text("SELECT current_database(), current_user"))
    db_info = result.first()
    print(f"Connected to database: {db_info[0]} as user: {db_info[1]}")
    
    # List all tables
    result = session.exec(text("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name
    """))
    tables = [row[0] for row in result.all()]
    print(f"Available tables: {tables}")
    
    # Check if campaignbriefing table exists
    assert "campaignbriefing" in tables, f"campaignbriefing table not found. Available tables: {tables}" 

def test_campaignbriefing_table_exists_in_ci(session: Session):
    """Test that the campaignbriefing table exists in CI environment."""
    import os
    if os.getenv('GITHUB_ACTIONS') == 'true':
        # In CI, check if the table exists
        from sqlmodel import text
        result = session.exec(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'campaignbriefing'
            )
        """))
        table_exists = result.first()[0]
        assert table_exists, "campaignbriefing table does not exist in CI database"
        
        # Also check if we can query it
        result = session.exec(text("SELECT COUNT(*) FROM campaignbriefing"))
        count = result.first()[0]
        print(f"campaignbriefing table has {count} rows")
    else:
        # In local development, this test is not relevant
        pytest.skip("This test is only relevant in CI environment") 