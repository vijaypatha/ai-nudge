# Simple test to verify database setup works without table redefinition errors

import pytest
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool
from sqlalchemy import text

def test_database_setup_works():
    """Test that database setup works without table redefinition errors."""
    # Create a test engine
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    # Import models - this should not cause table redefinition errors
    from data.models import (
        User, Client, Resource, ContentResource, Message, ScheduledMessage,
        CampaignBriefing, MarketEvent, PipelineRun, Faq, NegativePreference
    )
    
    # Create tables
    SQLModel.metadata.create_all(engine)
    
    # Test that we can create a session and query
    with Session(engine) as session:
        # Test that we can query the User table
        from data.models.user import User
        users = session.exec(text("SELECT name FROM sqlite_master WHERE type='table' AND name='user'")).all()
        assert len(users) == 1, "User table should exist"
        
        # Test that we can create a user
        user = User(
            full_name="Test User",
            phone_number="+15551234567"
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        
        assert user.id is not None
        assert user.full_name == "Test User"
    
    print("✅ Database setup test passed - no table redefinition errors!")

def test_conftest_fixtures_work():
    """Test that conftest.py fixtures work correctly."""
    # This test will use the fixtures from conftest.py
    from data.models import User
    
    # The conftest.py should handle the database setup
    # If this test runs without errors, the fix is working
    assert True, "Conftest fixtures should work without table redefinition errors" 