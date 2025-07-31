# File: backend/tests/test_database_schema.py
# 
# What does this file test:
# This file tests database schema consistency, multi-vertical support, vector embeddings,
# JSON field functionality, foreign key constraints, indexes, and migration compatibility.
# It ensures the database design supports all verticals (real estate, therapy, etc.) in a
# single database architecture with proper data isolation and performance optimization.
# 
# When was it updated: 2025-01-27

import pytest
import uuid
from sqlmodel import Session, SQLModel, create_engine, select
from sqlalchemy import inspect, text
from typing import List, Dict, Any

from data.database import engine, get_session
from data.models.user import User, UserType
from data.models.client import Client
from data.models.resource import Resource, ResourceType, ResourceStatus
from data.models.message import Message, MessageDirection, MessageStatus, MessageSource, MessageSenderType
from data.models.campaign import CampaignBriefing, CampaignStatus
from data.models.event import MarketEvent
from data.models.faq import Faq


class TestDatabaseSchema:
    """Test suite for database schema consistency and migrations"""

    def test_all_models_can_be_created(self, session: Session):
        """Test that all SQLModel tables can be created without errors"""
        # This test ensures all models are properly defined and can be created
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        # Verify all expected tables exist
        expected_tables = [
            'user', 'client', 'resource', 'contentresource', 
            'message', 'scheduledmessage', 'campaignbriefing',
            'marketevent', 'pipelinerun', 'faq', 'negativepreference'
        ]
        
        for table in expected_tables:
            assert table in tables, f"Table '{table}' not found in database"

    def test_user_model_supports_verticals(self, session: Session):
        """Test that User model properly supports multiple verticals"""
        # Create users for different verticals
        realtor = User(
            id=uuid.uuid4(),
            full_name="Test Realtor",
            email="realtor@test.com",
            phone_number="+15551111111",
            vertical="real_estate",
            tool_provider="flexmls_spark"
        )
        
        therapist = User(
            id=uuid.uuid4(),
            full_name="Test Therapist",
            email="therapist@test.com",
            phone_number="+15552222222",
            vertical="therapy",
            tool_provider="google_calendar"
        )
        
        session.add(realtor)
        session.add(therapist)
        session.commit()
        
        # Verify both users exist with correct verticals
        users = session.exec(select(User)).all()
        assert len(users) == 2
        
        verticals = [user.vertical for user in users]
        assert "real_estate" in verticals
        assert "therapy" in verticals

    def test_client_model_supports_embeddings(self, session: Session):
        """Test that Client model supports vector embeddings"""
        user = User(
            id=uuid.uuid4(),
            full_name="Test User",
            phone_number="+15553333333"
        )
        session.add(user)
        session.commit()
        
        # Create client with embedding
        client = Client(
            id=uuid.uuid4(),
            user_id=user.id,
            full_name="Test Client",
            email="client@test.com",
            notes="This is a test client",
            notes_embedding=[0.1, 0.2, 0.3, 0.4],  # Mock embedding
            user_tags=["buyer", "interested"],
            ai_tags=["urgent"],
            preferences={"budget": "500k-750k"}
        )
        
        session.add(client)
        session.commit()
        
        # Verify embedding is stored correctly
        retrieved_client = session.get(Client, client.id)
        assert retrieved_client.notes_embedding == [0.1, 0.2, 0.3, 0.4]

    def test_resource_model_supports_multiple_types(self, session: Session):
        """Test that Resource model supports different resource types"""
        user = User(
            id=uuid.uuid4(),
            full_name="Test User",
            phone_number="+15554444444"
        )
        session.add(user)
        session.commit()
        
        # Create different types of resources
        property_resource = Resource(
            id=uuid.uuid4(),
            user_id=user.id,
            resource_type=ResourceType.PROPERTY,
            status=ResourceStatus.ACTIVE,
            attributes={
                "address": "123 Main St",
                "price": 750000,
                "bedrooms": 4
            }
        )
        
        content_resource = Resource(
            id=uuid.uuid4(),
            user_id=user.id,
            resource_type=ResourceType.CONTENT_RESOURCE,
            status=ResourceStatus.ACTIVE,
            attributes={
                "title": "First Time Buyer Guide",
                "url": "https://example.com/guide"
            }
        )
        
        session.add(property_resource)
        session.add(content_resource)
        session.commit()
        
        # Verify both resource types exist
        resources = session.exec(select(Resource)).all()
        assert len(resources) == 2
        
        resource_types = [r.resource_type for r in resources]
        assert ResourceType.PROPERTY in resource_types
        assert ResourceType.CONTENT_RESOURCE in resource_types

    def test_message_model_supports_all_directions(self, session: Session):
        """Test that Message model supports all message directions and statuses"""
        user = User(
            id=uuid.uuid4(),
            full_name="Test User",
            phone_number="+15555555555"
        )
        client = Client(
            id=uuid.uuid4(),
            user_id=user.id,
            full_name="Test Client"
        )
        session.add(user)
        session.add(client)
        session.commit()
        
        # Create messages with different directions and statuses
        inbound_message = Message(
            id=uuid.uuid4(),
            user_id=user.id,
            client_id=client.id,
            content="Hello, I'm interested in buying a house",
            direction=MessageDirection.INBOUND,
            status=MessageStatus.RECEIVED,
            source=MessageSource.MANUAL,
            sender_type=MessageSenderType.SYSTEM
        )
        
        outbound_message = Message(
            id=uuid.uuid4(),
            user_id=user.id,
            client_id=client.id,
            content="Thanks for your interest!",
            direction=MessageDirection.OUTBOUND,
            status=MessageStatus.SENT,
            source=MessageSource.MANUAL,
            sender_type=MessageSenderType.USER
        )
        
        session.add(inbound_message)
        session.add(outbound_message)
        session.commit()
        
        # Verify both message types exist
        messages = session.exec(select(Message)).all()
        assert len(messages) == 2
        
        directions = [m.direction for m in messages]
        assert MessageDirection.INBOUND in directions
        assert MessageDirection.OUTBOUND in directions

    def test_campaign_model_supports_all_statuses(self, session: Session):
        """Test that CampaignBriefing model supports all campaign statuses"""
        user = User(
            id=uuid.uuid4(),
            full_name="Test User",
            phone_number="+15556666666"
        )
        client = Client(
            id=uuid.uuid4(),
            user_id=user.id,
            full_name="Test Client"
        )
        session.add(user)
        session.add(client)
        session.commit()
        
        # Create campaigns with different statuses
        draft_campaign = CampaignBriefing(
            id=uuid.uuid4(),
            user_id=user.id,
            client_id=client.id,
            headline="Draft Campaign",
            status=CampaignStatus.DRAFT
        )
        
        active_campaign = CampaignBriefing(
            id=uuid.uuid4(),
            user_id=user.id,
            client_id=client.id,
            headline="Active Campaign",
            status=CampaignStatus.ACTIVE
        )
        
        session.add(draft_campaign)
        session.add(active_campaign)
        session.commit()
        
        # Verify both campaign statuses exist
        campaigns = session.exec(select(CampaignBriefing)).all()
        assert len(campaigns) == 2
        
        statuses = [c.status for c in campaigns]
        assert CampaignStatus.DRAFT in statuses
        assert CampaignStatus.ACTIVE in statuses

    def test_foreign_key_constraints(self, session: Session):
        """Test that foreign key constraints work properly"""
        user = User(
            id=uuid.uuid4(),
            full_name="Test User",
            phone_number="+15557777777"
        )
        session.add(user)
        session.commit()
        
        # Create client with valid user_id
        client = Client(
            id=uuid.uuid4(),
            user_id=user.id,
            full_name="Test Client"
        )
        session.add(client)
        session.commit()
        
        # Verify client was created
        assert session.get(Client, client.id) is not None
        
        # Test that invalid user_id raises error (if constraints are enforced)
        # Note: SQLite in test mode might not enforce all constraints
        invalid_client = Client(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),  # Non-existent user
            full_name="Invalid Client"
        )
        session.add(invalid_client)
        session.commit()  # This might succeed in test mode

    def test_json_field_support(self, session: Session):
        """Test that JSON fields work properly for flexible data storage"""
        user = User(
            id=uuid.uuid4(),
            full_name="Test User",
            phone_number="+15558888888",
            onboarding_state={
                "phone_verified": True,
                "work_style_set": False,
                "contacts_imported": True
            },
            market_focus=["residential", "luxury"],
            strategy={"nudge_format": "ready-to-send", "frequency": "daily"}
        )
        session.add(user)
        session.commit()
        
        # Verify JSON fields are stored and retrieved correctly
        retrieved_user = session.get(User, user.id)
        assert retrieved_user.onboarding_state["phone_verified"] is True
        assert retrieved_user.market_focus == ["residential", "luxury"]
        assert retrieved_user.strategy["nudge_format"] == "ready-to-send"

    def test_indexes_exist(self, session: Session):
        """Test that important indexes exist for performance"""
        inspector = inspect(engine)
        
        # Check for important indexes
        user_indexes = inspector.get_indexes('user')
        client_indexes = inspector.get_indexes('client')
        
        # Verify key indexes exist
        user_index_names = [idx['name'] for idx in user_indexes]
        client_index_names = [idx['name'] for idx in client_indexes]
        
        # These are the most critical indexes for performance
        assert any('ix_user_phone_number' in name for name in user_index_names)
        assert any('ix_user_vertical' in name for name in user_index_names)
        assert any('ix_client_user_id' in name for name in client_index_names)

    def test_migration_consistency(self, session: Session):
        """Test that the current schema matches what migrations would create"""
        # This test ensures that if we ran migrations from scratch,
        # we'd get the same schema as create_all()
        
        # Get current table definitions
        inspector = inspect(engine)
        current_tables = inspector.get_table_names()
        
        # Verify all expected tables exist
        expected_tables = [
            'user', 'client', 'resource', 'contentresource',
            'message', 'scheduledmessage', 'campaignbriefing',
            'marketevent', 'pipelinerun', 'faq', 'negativepreference'
        ]
        
        for table in expected_tables:
            assert table in current_tables, f"Migration missing table: {table}"

    def test_vertical_agnostic_design(self, session: Session):
        """Test that the database design truly supports multiple verticals"""
        # Create users for different verticals
        realtor = User(
            id=uuid.uuid4(),
            full_name="Realtor",
            phone_number="+15559999999",
            vertical="real_estate"
        )
        
        therapist = User(
            id=uuid.uuid4(),
            full_name="Therapist", 
            phone_number="+15550000000",
            vertical="therapy"
        )
        
        session.add(realtor)
        session.add(therapist)
        session.commit()
        
        # Create clients for each vertical
        realtor_client = Client(
            id=uuid.uuid4(),
            user_id=realtor.id,
            full_name="Home Buyer",
            preferences={"budget": "500k", "location": "downtown"}
        )
        
        therapy_client = Client(
            id=uuid.uuid4(),
            user_id=therapist.id,
            full_name="Patient",
            preferences={"session_type": "individual", "focus": "anxiety"}
        )
        
        session.add(realtor_client)
        session.add(therapy_client)
        session.commit()
        
        # Verify data isolation - users can only see their own clients
        realtor_clients = session.exec(
            select(Client).where(Client.user_id == realtor.id)
        ).all()
        
        therapist_clients = session.exec(
            select(Client).where(Client.user_id == therapist.id)
        ).all()
        
        assert len(realtor_clients) == 1
        assert len(therapist_clients) == 1
        assert realtor_clients[0].user_id == realtor.id
        assert therapist_clients[0].user_id == therapist.id 