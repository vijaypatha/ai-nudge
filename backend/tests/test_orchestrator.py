# File: backend/tests/test_orchestrator.py
# 
# What does this file test:
# This file tests the orchestrator service which coordinates AI agents, CRM operations,
# message handling, and client intelligence updates. It validates conversation processing,
# recommendation generation, tag extraction, draft suggestions, and the overall workflow
# orchestration between different AI agents and services.
# 
# When was it updated: 2025-01-27

import pytest
import uuid
import asyncio
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock, AsyncMock
from sqlmodel import Session

from data.models.user import User
from data.models.client import Client
from data.models.message import Message, MessageDirection, MessageStatus, MessageSource, MessageSenderType
from data.models.campaign import CampaignBriefing, CampaignStatus, CoPilotAction
from agent_core.orchestrator import handle_incoming_message, orchestrate_send_message_now, _cleanup_duplicate_cache


class TestHandleIncomingMessage:
    """Test suite for handle_incoming_message function"""

    @pytest.fixture
    def mock_user(self) -> User:
        """Create a test user with required fields"""
        return User(
            id=uuid.uuid4(),
            full_name="Test User",
            email="test@example.com",
            phone_number="+15551234567",
            twilio_phone_number="+15551234567",
            vertical="real_estate"
        )

    @pytest.fixture
    def mock_client(self, mock_user: User) -> Client:
        """Create a test client"""
        return Client(
            id=uuid.uuid4(),
            user_id=mock_user.id,
            full_name="Test Client",
            email="client@test.com",
            phone="+15558887777"
        )

    @pytest.fixture
    def mock_incoming_message(self, mock_user: User, mock_client: Client) -> Message:
        """Create a mock incoming message"""
        return Message(
            id=uuid.uuid4(),
            user_id=mock_user.id,
            client_id=mock_client.id,
            content="Hello, I'm interested in buying a house",
            direction=MessageDirection.INBOUND,
            status=MessageStatus.RECEIVED,
            source=MessageSource.MANUAL,
            sender_type=MessageSenderType.SYSTEM,
            created_at=datetime.now(timezone.utc)
        )

    @pytest.mark.asyncio
    @patch('agent_core.orchestrator.websocket_manager')
    @patch('agent_core.orchestrator.conversation_agent')
    @patch('agent_core.orchestrator.crm_service')
    @patch('agent_core.orchestrator.get_playbook_for_intent')
    @patch('agent_core.orchestrator.Session')
    async def test_handle_incoming_message_standard_flow(
        self, 
        mock_session_class,
        mock_get_playbook, 
        mock_crm_service, 
        mock_conversation_agent, 
        mock_websocket_manager,
        mock_user: User,
        mock_client: Client,
        mock_incoming_message: Message
    ):
        """Test standard incoming message processing flow"""
        # Setup mocks
        mock_crm_service.get_recent_messages.return_value = []
        mock_crm_service.get_client_by_id.return_value = mock_client
        mock_crm_service.update_client_intel = AsyncMock()
        mock_conversation_agent.generate_recommendation_slate = AsyncMock(return_value={
            "recommendations": [{"type": "SUGGEST_DRAFT", "payload": {"text": "Test draft"}}],
            "tags": ["interested", "buyer"]
        })
        mock_conversation_agent.detect_conversational_intent = AsyncMock(return_value="buy_intent")
        mock_get_playbook.return_value = None
        mock_websocket_manager.broadcast_json_to_client = AsyncMock()

        # Mock the database session
        mock_session = MagicMock()
        mock_session.exec.return_value.first.return_value = None  # No active plan
        mock_session_class.return_value.__enter__.return_value = mock_session

        # Execute
        result = await handle_incoming_message(
            client_id=mock_client.id,
            incoming_message=mock_incoming_message,
            user=mock_user
        )

        # Assertions
        assert result["status"] == "processed"
        mock_crm_service.update_last_interaction.assert_called_once()
        mock_conversation_agent.generate_recommendation_slate.assert_called_once()
        mock_conversation_agent.detect_conversational_intent.assert_called_once()
        mock_websocket_manager.broadcast_json_to_client.assert_called_once()

    @pytest.mark.asyncio
    @patch('agent_core.orchestrator.websocket_manager')
    @patch('agent_core.orchestrator.conversation_agent')
    @patch('agent_core.orchestrator.crm_service')
    @patch('agent_core.orchestrator.Session')
    async def test_handle_incoming_message_with_active_plan_pause_and_propose(
        self,
        mock_session_class,
        mock_crm_service,
        mock_conversation_agent,
        mock_websocket_manager,
        mock_user: User,
        mock_client: Client,
        mock_incoming_message: Message
    ):
        """Test pause and propose logic when active plan exists"""
        # Create an active plan
        active_plan = CampaignBriefing(
            id=uuid.uuid4(),
            user_id=mock_user.id,
            client_id=mock_client.id,
            status=CampaignStatus.ACTIVE,
            is_plan=True,
            campaign_type="test_campaign",
            headline="Test Plan",
            key_intel={},
            original_draft="Test draft"
        )

        # Setup mocks
        mock_crm_service.cancel_scheduled_messages_for_plan = MagicMock()
        mock_crm_service.save_campaign_briefing = MagicMock()
        mock_websocket_manager.broadcast_json_to_client = AsyncMock()

        # Mock the database session to return the active plan
        mock_session = MagicMock()
        mock_session.exec.return_value.first.return_value = active_plan
        mock_session_class.return_value.__enter__.return_value = mock_session

        # Execute
        result = await handle_incoming_message(
            client_id=mock_client.id,
            incoming_message=mock_incoming_message,
            user=mock_user
        )

        # Assertions
        assert result["status"] == "paused_and_proposed"
        mock_crm_service.cancel_scheduled_messages_for_plan.assert_called_once()
        mock_crm_service.save_campaign_briefing.assert_called_once()
        mock_websocket_manager.broadcast_json_to_client.assert_called_once()

    @pytest.mark.asyncio
    @patch('agent_core.orchestrator.conversation_agent')
    @patch('agent_core.orchestrator.crm_service')
    @patch('agent_core.orchestrator.Session')
    async def test_handle_incoming_message_faq_detection(
        self,
        mock_session_class,
        mock_crm_service,
        mock_conversation_agent,
        mock_user: User,
        mock_client: Client
    ):
        """Test FAQ detection logic"""
        # Create FAQ-style message
        faq_message = Message(
            id=uuid.uuid4(),
            user_id=mock_user.id,
            client_id=mock_client.id,
            content="What's the price?",
            direction=MessageDirection.INBOUND,
            status=MessageStatus.RECEIVED,
            source=MessageSource.MANUAL,
            sender_type=MessageSenderType.SYSTEM,
            created_at=datetime.now(timezone.utc)
        )

        # Mock the database query to return None (no active plan)
        mock_session = MagicMock()
        mock_session.exec.return_value.first.return_value = None
        mock_session_class.return_value.__enter__.return_value = mock_session

        # Execute
        result = await handle_incoming_message(
            client_id=mock_client.id,
            incoming_message=faq_message,
            user=mock_user
        )

        # Assertions
        assert result["status"] == "processed_as_faq"
        # Should not call conversation agent for FAQ messages
        mock_conversation_agent.generate_recommendation_slate.assert_not_called()

    @pytest.mark.asyncio
    @patch('agent_core.orchestrator.websocket_manager')
    @patch('agent_core.orchestrator.conversation_agent')
    @patch('agent_core.orchestrator.crm_service')
    @patch('agent_core.orchestrator.get_playbook_for_intent')
    @patch('agent_core.orchestrator.Session')
    async def test_handle_incoming_message_with_playbook_detection(
        self,
        mock_session_class,
        mock_get_playbook,
        mock_crm_service,
        mock_conversation_agent,
        mock_websocket_manager,
        mock_user: User,
        mock_client: Client,
        mock_incoming_message: Message
    ):
        """Test playbook detection and campaign planning"""
        # Setup mock playbook
        mock_playbook = MagicMock()
        mock_playbook.name = "Test Playbook"
        mock_playbook.intent_type = "buy_intent"
        mock_playbook.steps = [
            MagicMock(prompt="Step 1", delay_days=1),
            MagicMock(prompt="Step 2", delay_days=3)
        ]
        mock_get_playbook.return_value = mock_playbook

        # Setup other mocks
        mock_crm_service.get_recent_messages.return_value = []
        mock_crm_service.get_client_by_id.return_value = mock_client
        mock_conversation_agent.generate_recommendation_slate = AsyncMock(return_value={
            "recommendations": [{"type": "SUGGEST_DRAFT", "payload": {"text": "Test draft"}}]
        })
        mock_conversation_agent.detect_conversational_intent = AsyncMock(return_value="buy_intent")
        mock_conversation_agent.draft_campaign_step_message = AsyncMock(return_value=("Test draft", 1))
        mock_crm_service.save_campaign_briefing = MagicMock()
        mock_websocket_manager.broadcast_json_to_client = AsyncMock()

        # Mock the database session to return None for active plan query
        mock_session = MagicMock()
        mock_session.exec.return_value.first.return_value = None  # No active plan
        mock_session_class.return_value.__enter__.return_value = mock_session

        # Execute
        result = await handle_incoming_message(
            client_id=mock_client.id,
            incoming_message=mock_incoming_message,
            user=mock_user
        )

        # Assertions
        assert result["status"] == "processed"
        mock_get_playbook.assert_called_once_with("buy_intent", "real_estate")
        mock_conversation_agent.draft_campaign_step_message.assert_called()
        mock_crm_service.save_campaign_briefing.assert_called()

    @pytest.mark.asyncio
    @patch('agent_core.orchestrator.conversation_agent')
    @patch('agent_core.orchestrator.crm_service')
    @patch('agent_core.orchestrator.Session')
    async def test_handle_incoming_message_error_handling(
        self,
        mock_session_class,
        mock_crm_service,
        mock_conversation_agent,
        mock_user: User,
        mock_client: Client,
        mock_incoming_message: Message
    ):
        """Test error handling in incoming message processing"""
        # Setup mock to raise exception
        mock_crm_service.get_client_by_id.side_effect = ValueError("Client not found")

        # Mock the database session
        mock_session = MagicMock()
        mock_session.exec.return_value.first.return_value = None
        mock_session_class.return_value.__enter__.return_value = mock_session

        # Execute
        result = await handle_incoming_message(
            client_id=mock_client.id,
            incoming_message=mock_incoming_message,
            user=mock_user
        )

        # Assertions
        assert result["status"] == "error"

    @pytest.mark.asyncio
    @patch('agent_core.orchestrator.websocket_manager')
    @patch('agent_core.orchestrator.conversation_agent')
    @patch('agent_core.orchestrator.crm_service')
    @patch('agent_core.orchestrator.Session')
    async def test_handle_incoming_message_websocket_error_handling(
        self,
        mock_session_class,
        mock_crm_service,
        mock_conversation_agent,
        mock_websocket_manager,
        mock_user: User,
        mock_client: Client,
        mock_incoming_message: Message
    ):
        """Test websocket broadcast error handling"""
        # Setup mocks
        mock_crm_service.get_recent_messages.return_value = []
        mock_crm_service.get_client_by_id.return_value = mock_client
        mock_conversation_agent.generate_recommendation_slate = AsyncMock(return_value={
            "recommendations": [{"type": "SUGGEST_DRAFT", "payload": {"text": "Test draft"}}]
        })
        mock_conversation_agent.detect_conversational_intent = AsyncMock(return_value=None)
        mock_websocket_manager.broadcast_json_to_client = AsyncMock(side_effect=Exception("WebSocket error"))

        # Mock the database session
        mock_session = MagicMock()
        mock_session.exec.return_value.first.return_value = None
        mock_session_class.return_value.__enter__.return_value = mock_session

        # Execute
        result = await handle_incoming_message(
            client_id=mock_client.id,
            incoming_message=mock_incoming_message,
            user=mock_user
        )

        # Assertions
        assert result["status"] == "processed"
        # Should not fail the entire operation due to websocket error

    @pytest.mark.asyncio
    @patch('agent_core.orchestrator.websocket_manager')
    @patch('agent_core.orchestrator.conversation_agent')
    @patch('agent_core.orchestrator.crm_service')
    @patch('agent_core.orchestrator.Session')
    async def test_handle_incoming_message_with_tags_extraction(
        self,
        mock_session_class,
        mock_crm_service,
        mock_conversation_agent,
        mock_websocket_manager,
        mock_user: User,
        mock_client: Client,
        mock_incoming_message: Message
    ):
        """Test tag extraction from recommendation data"""
        # Setup mocks
        mock_crm_service.get_recent_messages.return_value = []
        mock_crm_service.get_client_by_id.return_value = mock_client
        mock_crm_service.update_client_intel = AsyncMock()
        mock_conversation_agent.generate_recommendation_slate = AsyncMock(return_value={
            "recommendations": [
                {"type": "SUGGEST_DRAFT", "payload": {"text": "Test draft"}},
                {"type": "UPDATE_CLIENT_INTEL", "payload": {"tags_to_add": ["interested", "buyer", "urgent"]}}
            ]
        })
        mock_conversation_agent.detect_conversational_intent = AsyncMock(return_value=None)
        mock_websocket_manager.broadcast_json_to_client = AsyncMock()

        # Mock the database session
        mock_session = MagicMock()
        mock_session.exec.return_value.first.return_value = None
        mock_session_class.return_value.__enter__.return_value = mock_session

        # Execute
        result = await handle_incoming_message(
            client_id=mock_client.id,
            incoming_message=mock_incoming_message,
            user=mock_user
        )

        # Assertions
        assert result["status"] == "processed"
        mock_crm_service.update_client_intel.assert_called_once_with(
            client_id=mock_client.id,
            user_id=mock_user.id,
            tags_to_add=["interested", "buyer", "urgent"],
            notes_to_add=None
        )

    @pytest.mark.asyncio
    @patch('agent_core.orchestrator.websocket_manager')
    @patch('agent_core.orchestrator.conversation_agent')
    @patch('agent_core.orchestrator.crm_service')
    @patch('agent_core.orchestrator.Session')
    async def test_handle_incoming_message_no_recommendations(
        self,
        mock_session_class,
        mock_crm_service,
        mock_conversation_agent,
        mock_websocket_manager,
        mock_user: User,
        mock_client: Client,
        mock_incoming_message: Message
    ):
        """Test handling when no recommendations are generated"""
        # Setup mocks
        mock_crm_service.get_recent_messages.return_value = []
        mock_crm_service.get_client_by_id.return_value = mock_client
        mock_conversation_agent.generate_recommendation_slate = AsyncMock(return_value=None)
        mock_conversation_agent.detect_conversational_intent = AsyncMock(return_value=None)
        mock_websocket_manager.broadcast_json_to_client = AsyncMock()

        # Mock the database session
        mock_session = MagicMock()
        mock_session.exec.return_value.first.return_value = None
        mock_session_class.return_value.__enter__.return_value = mock_session

        # Execute
        result = await handle_incoming_message(
            client_id=mock_client.id,
            incoming_message=mock_incoming_message,
            user=mock_user
        )

        # Assertions
        assert result["status"] == "processed"
        # Should not call websocket broadcast when no recommendations
        mock_websocket_manager.broadcast_json_to_client.assert_not_called()


class TestOrchestrateSendMessageNow:
    """Test suite for orchestrate_send_message_now function"""

    @pytest.fixture
    def mock_user_with_twilio(self) -> User:
        """Create a test user with Twilio number"""
        return User(
            id=uuid.uuid4(),
            full_name="Test User",
            email="test@example.com",
            phone_number="+15551234567",
            twilio_phone_number="+15551234567"
        )

    @pytest.fixture
    def mock_client_with_phone(self, mock_user_with_twilio: User) -> Client:
        """Create a test client with phone number"""
        return Client(
            id=uuid.uuid4(),
            user_id=mock_user_with_twilio.id,
            full_name="Test Client",
            email="client@test.com",
            phone="+15558887777"
        )

    @pytest.mark.asyncio
    async def test_orchestrate_send_message_now_empty_content(
        self,
        mock_user_with_twilio: User,
        mock_client_with_phone: Client
    ):
        """Test handling of empty message content"""
        result = await orchestrate_send_message_now(
            client_id=mock_client_with_phone.id,
            content="",
            user_id=mock_user_with_twilio.id
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_orchestrate_send_message_now_invalid_ids(
        self
    ):
        """Test handling of invalid client_id or user_id"""
        result = await orchestrate_send_message_now(
            client_id=None,
            content="Test message",
            user_id=None
        )
        assert result is None

    @pytest.mark.asyncio
    @patch('agent_core.orchestrator.crm_service')
    async def test_orchestrate_send_message_now_user_not_found(
        self,
        mock_crm_service,
        mock_client_with_phone: Client
    ):
        """Test handling when user is not found"""
        mock_crm_service.get_user_by_id.return_value = None

        result = await orchestrate_send_message_now(
            client_id=mock_client_with_phone.id,
            content="Test message",
            user_id=uuid.uuid4()
        )
        assert result is None

    @pytest.mark.asyncio
    @patch('agent_core.orchestrator.crm_service')
    async def test_orchestrate_send_message_now_client_not_found(
        self,
        mock_crm_service,
        mock_user_with_twilio: User
    ):
        """Test handling when client is not found"""
        mock_crm_service.get_user_by_id.return_value = mock_user_with_twilio
        mock_crm_service.get_client_by_id.return_value = None

        result = await orchestrate_send_message_now(
            client_id=uuid.uuid4(),
            content="Test message",
            user_id=mock_user_with_twilio.id
        )
        assert result is None

    @pytest.mark.asyncio
    @patch('agent_core.orchestrator.twilio_outgoing')
    @patch('agent_core.orchestrator.crm_service')
    async def test_orchestrate_send_message_now_twilio_all_retries_fail(
        self,
        mock_crm_service,
        mock_twilio_outgoing,
        mock_user_with_twilio: User,
        mock_client_with_phone: Client
    ):
        """Test when all Twilio retries fail"""
        # Setup mocks
        mock_crm_service.get_user_by_id.return_value = mock_user_with_twilio
        mock_crm_service.get_client_by_id.return_value = mock_client_with_phone
        mock_crm_service.get_recent_messages.return_value = []

        # Mock twilio to always fail
        mock_twilio_outgoing.send_sms.return_value = False

        # Execute
        result = await orchestrate_send_message_now(
            client_id=mock_client_with_phone.id,
            content="Test message that fails",
            user_id=mock_user_with_twilio.id
        )

        # Assertions
        assert result is None
        assert mock_twilio_outgoing.send_sms.call_count == 3

    @pytest.mark.asyncio
    @patch('agent_core.orchestrator.crm_service')
    async def test_orchestrate_send_message_now_duplicate_detection_cache(
        self,
        mock_crm_service,
        mock_user_with_twilio: User,
        mock_client_with_phone: Client
    ):
        """Test duplicate message detection using cache"""
        # First call to populate cache
        mock_crm_service.get_user_by_id.return_value = mock_user_with_twilio
        mock_crm_service.get_client_by_id.return_value = mock_client_with_phone
        mock_crm_service.get_recent_messages.return_value = []

        # Mock twilio to succeed
        with patch('agent_core.orchestrator.twilio_outgoing') as mock_twilio:
            mock_twilio.send_sms.return_value = True
            
            # Mock session to avoid database connection
            with patch('agent_core.orchestrator.Session') as mock_session_class:
                mock_session = MagicMock()
                mock_session_class.return_value.__enter__.return_value = mock_session
                
                # First message
                result1 = await orchestrate_send_message_now(
                    client_id=mock_client_with_phone.id,
                    content="Duplicate test message",
                    user_id=mock_user_with_twilio.id
                )
                assert result1 is not None

                # Second identical message within cache window
                result2 = await orchestrate_send_message_now(
                    client_id=mock_client_with_phone.id,
                    content="Duplicate test message",
                    user_id=mock_user_with_twilio.id
                )
                assert result2 is None  # Should be blocked by cache

    @pytest.mark.asyncio
    @patch('agent_core.orchestrator.twilio_outgoing')
    @patch('agent_core.orchestrator.crm_service')
    async def test_orchestrate_send_message_now_duplicate_detection_database(
        self,
        mock_crm_service,
        mock_twilio_outgoing,
        mock_user_with_twilio: User,
        mock_client_with_phone: Client
    ):
        """Test duplicate message detection using database"""
        # Create a recent duplicate message in database
        recent_message = Message(
            id=uuid.uuid4(),
            user_id=mock_user_with_twilio.id,
            client_id=mock_client_with_phone.id,
            content="Duplicate test message",
            direction=MessageDirection.OUTBOUND,
            status=MessageStatus.SENT,
            source=MessageSource.MANUAL,
            created_at=datetime.now(timezone.utc) - timedelta(minutes=2)  # Recent
        )

        # Setup mocks
        mock_crm_service.get_user_by_id.return_value = mock_user_with_twilio
        mock_crm_service.get_client_by_id.return_value = mock_client_with_phone
        mock_crm_service.get_recent_messages.return_value = [recent_message]

        # Try to send duplicate
        result = await orchestrate_send_message_now(
            client_id=mock_client_with_phone.id,
            content="Duplicate test message",
            user_id=mock_user_with_twilio.id,
            source=MessageSource.MANUAL
        )

        # Should return the existing message instead of creating new one
        assert result is not None
        assert result.id == recent_message.id
        mock_twilio_outgoing.send_sms.assert_not_called()

    @pytest.mark.asyncio
    @patch('agent_core.orchestrator.twilio_outgoing')
    @patch('agent_core.orchestrator.crm_service')
    async def test_orchestrate_send_message_now_successful_send(
        self,
        mock_crm_service,
        mock_twilio_outgoing,
        mock_user_with_twilio: User,
        mock_client_with_phone: Client
    ):
        """Test successful message sending with personalization"""
        # Setup mocks
        mock_crm_service.get_user_by_id.return_value = mock_user_with_twilio
        mock_crm_service.get_client_by_id.return_value = mock_client_with_phone
        mock_crm_service.get_recent_messages.return_value = []
        mock_crm_service.update_last_interaction = MagicMock()
        mock_crm_service.get_all_active_slates_for_client = MagicMock(return_value=[])
        mock_twilio_outgoing.send_sms.return_value = True

        # Mock session to avoid database connection
        with patch('agent_core.orchestrator.Session') as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value.__enter__.return_value = mock_session

            # Execute
            result = await orchestrate_send_message_now(
                client_id=mock_client_with_phone.id,
                content="Hello [Client Name], how are you?",
                user_id=mock_user_with_twilio.id
            )

            # Assertions
            assert result is not None
            assert result.content == "Hello Test, how are you?"  # Personalization applied
            assert result.direction == MessageDirection.OUTBOUND
            assert result.status == MessageStatus.SENT
            assert result.source == MessageSource.MANUAL
            assert result.sender_type == MessageSenderType.USER
            mock_twilio_outgoing.send_sms.assert_called_once_with(
                from_number=mock_user_with_twilio.twilio_phone_number,
                to_number=mock_client_with_phone.phone,
                body="Hello Test, how are you?"
            )

    @pytest.mark.asyncio
    @patch('agent_core.orchestrator.twilio_outgoing')
    @patch('agent_core.orchestrator.crm_service')
    async def test_orchestrate_send_message_now_retry_logic(
        self,
        mock_crm_service,
        mock_twilio_outgoing,
        mock_user_with_twilio: User,
        mock_client_with_phone: Client
    ):
        """Test Twilio retry logic with exponential backoff"""
        # Setup mocks
        mock_crm_service.get_user_by_id.return_value = mock_user_with_twilio
        mock_crm_service.get_client_by_id.return_value = mock_client_with_phone
        mock_crm_service.get_recent_messages.return_value = []
        mock_crm_service.update_last_interaction = MagicMock()
        mock_crm_service.get_all_active_slates_for_client = MagicMock(return_value=[])

        # Mock twilio to fail twice, then succeed
        mock_twilio_outgoing.send_sms.side_effect = [False, False, True]

        # Mock session to avoid database connection
        with patch('agent_core.orchestrator.Session') as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value.__enter__.return_value = mock_session

            # Execute
            result = await orchestrate_send_message_now(
                client_id=mock_client_with_phone.id,
                content="Test message with retries",
                user_id=mock_user_with_twilio.id
            )

            # Assertions
            assert result is not None
            assert mock_twilio_outgoing.send_sms.call_count == 3

    @pytest.mark.asyncio
    @patch('agent_core.orchestrator.twilio_outgoing')
    @patch('agent_core.orchestrator.crm_service')
    async def test_orchestrate_send_message_now_clear_recommendations(
        self,
        mock_crm_service,
        mock_twilio_outgoing,
        mock_user_with_twilio: User,
        mock_client_with_phone: Client
    ):
        """Test clearing active recommendations after sending"""
        # Create an active slate
        active_slate = CampaignBriefing(
            id=uuid.uuid4(),
            user_id=mock_user_with_twilio.id,
            client_id=mock_client_with_phone.id,
            status=CampaignStatus.ACTIVE,
            is_plan=False,
            campaign_type="test_slate",
            headline="Test Slate",
            key_intel={},
            original_draft="Test draft"
        )

        # Setup mocks
        mock_crm_service.get_user_by_id.return_value = mock_user_with_twilio
        mock_crm_service.get_client_by_id.return_value = mock_client_with_phone
        mock_crm_service.get_recent_messages.return_value = []
        mock_crm_service.update_last_interaction = MagicMock()
        mock_crm_service.get_all_active_slates_for_client = MagicMock(return_value=[active_slate])
        mock_crm_service.update_slate_status = MagicMock()
        mock_twilio_outgoing.send_sms.return_value = True

        # Mock session to avoid database connection
        with patch('agent_core.orchestrator.Session') as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value.__enter__.return_value = mock_session

            # Execute
            result = await orchestrate_send_message_now(
                client_id=mock_client_with_phone.id,
                content="Test message",
                user_id=mock_user_with_twilio.id
            )

            # Assertions
            assert result is not None
            # Fix: Use more flexible assertion since mock objects are different instances
            mock_crm_service.update_slate_status.assert_called()
            call_args = mock_crm_service.update_slate_status.call_args
            assert call_args[0][0] == active_slate.id  # slate_id
            assert call_args[0][1] == CampaignStatus.COMPLETED  # status
            assert call_args[0][2] == mock_user_with_twilio.id  # user_id
            # The session parameter is a mock object, so we just check it's called with 4 args
            assert len(call_args[0]) == 4

    @pytest.mark.asyncio
    @patch('agent_core.orchestrator.twilio_outgoing')
    @patch('agent_core.orchestrator.crm_service')
    async def test_orchestrate_send_message_now_database_error_handling(
        self,
        mock_crm_service,
        mock_twilio_outgoing,
        mock_user_with_twilio: User,
        mock_client_with_phone: Client
    ):
        """Test database error handling during message save"""
        # Setup mocks
        mock_crm_service.get_user_by_id.return_value = mock_user_with_twilio
        mock_crm_service.get_client_by_id.return_value = mock_client_with_phone
        mock_crm_service.get_recent_messages.return_value = []
        mock_twilio_outgoing.send_sms.return_value = True

        # Mock the engine to raise an exception when Session is created
        with patch('agent_core.orchestrator.engine') as mock_engine:
            mock_engine.side_effect = Exception("Database connection failed")
            
            # Execute
            result = await orchestrate_send_message_now(
                client_id=mock_client_with_phone.id,
                content="Test message",
                user_id=mock_user_with_twilio.id
            )

            # Assertions
            assert result is None

    @pytest.mark.asyncio
    @patch('agent_core.orchestrator.twilio_outgoing')
    @patch('agent_core.orchestrator.crm_service')
    async def test_orchestrate_send_message_now_old_duplicate_detection(
        self,
        mock_crm_service,
        mock_twilio_outgoing,
        mock_user_with_twilio: User,
        mock_client_with_phone: Client
    ):
        """Test duplicate detection for old messages (older than 5 minutes)"""
        # Create an old duplicate message in database
        old_message = Message(
            id=uuid.uuid4(),
            user_id=mock_user_with_twilio.id,
            client_id=mock_client_with_phone.id,
            content="Old duplicate message",
            direction=MessageDirection.OUTBOUND,
            status=MessageStatus.SENT,
            source=MessageSource.MANUAL,
            created_at=datetime.now(timezone.utc) - timedelta(minutes=10)  # Old
        )

        # Setup mocks
        mock_crm_service.get_user_by_id.return_value = mock_user_with_twilio
        mock_crm_service.get_client_by_id.return_value = mock_client_with_phone
        mock_crm_service.get_recent_messages.return_value = [old_message]
        mock_crm_service.update_last_interaction = MagicMock()
        mock_crm_service.get_all_active_slates_for_client = MagicMock(return_value=[])
        mock_twilio_outgoing.send_sms.return_value = True

        # Mock session to avoid database connection
        with patch('agent_core.orchestrator.Session') as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value.__enter__.return_value = mock_session

            # Try to send duplicate (should succeed since it's old)
            result = await orchestrate_send_message_now(
                client_id=mock_client_with_phone.id,
                content="Old duplicate message",
                user_id=mock_user_with_twilio.id,
                source=MessageSource.MANUAL
            )

            # Should create new message since old one is older than 5 minutes
            assert result is not None
            assert result.id != old_message.id
            mock_twilio_outgoing.send_sms.assert_called_once()


class TestDuplicateCacheCleanup:
    """Test suite for duplicate cache cleanup functionality"""

    def test_cleanup_duplicate_cache(self):
        """Test cleanup of old cache entries"""
        # Import the cache directly to test it
        from agent_core.orchestrator import _duplicate_send_cache
        
        # Clear the cache first
        _duplicate_send_cache.clear()
        
        # Add some test entries
        current_time = datetime.now(timezone.utc).timestamp()
        _duplicate_send_cache["old_entry"] = current_time - 400  # 6+ minutes old
        _duplicate_send_cache["new_entry"] = current_time - 60   # 1 minute old
        
        # Execute cleanup
        _cleanup_duplicate_cache()
        
        # Assertions
        assert "old_entry" not in _duplicate_send_cache
        assert "new_entry" in _duplicate_send_cache
        assert len(_duplicate_send_cache) == 1 