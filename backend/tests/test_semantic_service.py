# File: backend/tests/test_semantic_service.py
# 
# What does this file test:
# This file tests the semantic service functionality including vector index initialization,
# client embedding updates, semantic search, and similar client finding. It validates
# the AI-powered semantic matching system that uses vector embeddings to find
# similar clients and enable intelligent content recommendations.
# 
# When was it updated: 2025-01-27

import pytest
import uuid
import numpy as np
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime, timezone

from agent_core import semantic_service
from data.models.client import Client
from data.models.user import User
from sqlmodel import Session


class TestSemanticService:
    """Test suite for semantic service functionality"""

    @pytest.fixture
    def mock_user(self) -> User:
        """Create a test user"""
        return User(
            id=uuid.uuid4(),
            full_name="Test User",
            email="test@example.com",
            phone_number="+15551234567"
        )

    @pytest.fixture
    def mock_client(self, mock_user: User) -> Client:
        """Create a test client with embedding"""
        return Client(
            id=uuid.uuid4(),
            user_id=mock_user.id,
            full_name="Test Client",
            email="client@test.com",
            phone="+15558887777",
            notes_embedding=[0.1] * 1536  # Mock embedding
        )

    @pytest.mark.asyncio
    @patch('agent_core.semantic_service.crm_service')
    @patch('agent_core.semantic_service.generate_embedding')
    async def test_initialize_vector_index_success(self, mock_generate_embedding, mock_crm_service):
        """Test successful vector index initialization"""
        # Setup
        mock_clients = [
            Client(id=uuid.uuid4(), notes_embedding=[0.1] * 1536),
            Client(id=uuid.uuid4(), notes_embedding=[0.2] * 1536),
        ]
        mock_crm_service._get_all_clients_for_system_indexing.return_value = mock_clients

        # Execute
        await semantic_service.initialize_vector_index()

        # Assert
        mock_crm_service._get_all_clients_for_system_indexing.assert_called_once()
        assert semantic_service.faiss_index.ntotal == 2

    @pytest.mark.asyncio
    @patch('agent_core.semantic_service.crm_service')
    async def test_initialize_vector_index_empty(self, mock_crm_service):
        """Test vector index initialization with no clients"""
        # Setup
        mock_crm_service._get_all_clients_for_system_indexing.return_value = []

        # Execute
        await semantic_service.initialize_vector_index()

        # Assert
        assert semantic_service.faiss_index.ntotal == 0

    @pytest.mark.asyncio
    @patch('agent_core.semantic_service.crm_service')
    @patch('agent_core.semantic_service.generate_embedding')
    async def test_find_similar_clients_success(self, mock_generate_embedding, mock_crm_service):
        """Test finding similar clients"""
        # Setup
        user_id = uuid.uuid4()
        client_ids = [uuid.uuid4(), uuid.uuid4()]
        mock_clients = [
            Client(id=client_ids[0], user_id=user_id),
            Client(id=client_ids[1], user_id=user_id),
        ]
        
        # Mock the index to have some data
        semantic_service.faiss_index.add_with_ids(
            np.array([[0.1] * 1536, [0.2] * 1536]).astype('float32'),
            np.array([0, 1])
        )
        semantic_service.index_to_client_id_map = client_ids
        
        mock_generate_embedding.return_value = [0.15] * 1536
        mock_crm_service.get_all_clients.return_value = mock_clients

        # Execute
        result = await semantic_service.find_similar_clients("test query", user_id)

        # Assert
        assert isinstance(result, list)
        mock_generate_embedding.assert_called_once_with("test query")

    @pytest.mark.asyncio
    @patch('agent_core.semantic_service.crm_service')
    @patch('agent_core.semantic_service.generate_embedding')
    async def test_find_similar_clients_empty_index(self, mock_generate_embedding, mock_crm_service):
        """Test finding similar clients with empty index"""
        # Setup
        semantic_service.faiss_index.reset()
        semantic_service.index_to_client_id_map = []

        # Execute
        result = await semantic_service.find_similar_clients("test query", uuid.uuid4())

        # Assert
        assert result == []
        mock_generate_embedding.assert_not_called()

    @pytest.mark.asyncio
    @patch('agent_core.semantic_service.crm_service')
    @patch('agent_core.semantic_service.generate_embedding')
    async def test_update_client_embedding_success(self, mock_generate_embedding, mock_crm_service):
        """Test updating client embedding"""
        # Setup
        mock_client = Client(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            notes="Test notes",
            user_tags=["tag1", "tag2"],
            ai_tags=["ai_tag1"],
            preferences={"key": "value"}
        )
        mock_crm_service.get_recent_messages.return_value = []
        mock_generate_embedding.return_value = [0.1] * 1536
        mock_session = MagicMock()

        # Execute
        await semantic_service.update_client_embedding(mock_client, mock_session)

        # Assert
        mock_generate_embedding.assert_called_once()
        assert mock_client.notes_embedding == [0.1] * 1536

    @pytest.mark.asyncio
    @patch('agent_core.semantic_service.crm_service')
    async def test_update_client_embedding_invalid_client(self, mock_crm_service):
        """Test updating embedding for invalid client"""
        # Setup
        invalid_client = Client()  # Missing required fields
        mock_session = MagicMock()

        # Execute
        await semantic_service.update_client_embedding(invalid_client, mock_session)

        # Assert
        # Should not raise exception, just log warning
        assert invalid_client.notes_embedding is None

    @pytest.mark.asyncio
    @patch('agent_core.semantic_service.crm_service')
    @patch('agent_core.semantic_service.generate_embedding')
    async def test_update_client_embedding_with_conversation_context(self, mock_generate_embedding, mock_crm_service):
        """Test updating client embedding with conversation context"""
        # Setup
        from data.models.message import Message, MessageDirection, MessageStatus, MessageSource, MessageSenderType
        
        mock_client = Client(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            notes="Test notes",
            user_tags=["tag1"],
            ai_tags=[],
            preferences={}
        )
        
        mock_messages = [
            Message(
                id=uuid.uuid4(),
                content="Hello, I'm interested in buying a house",
                direction=MessageDirection.INBOUND,
                status=MessageStatus.RECEIVED,
                source=MessageSource.MANUAL,
                sender_type=MessageSenderType.SYSTEM
            )
        ]
        
        mock_crm_service.get_recent_messages.return_value = mock_messages
        mock_generate_embedding.return_value = [0.1] * 1536
        mock_session = MagicMock()

        # Execute
        await semantic_service.update_client_embedding(mock_client, mock_session)

        # Assert
        mock_crm_service.get_recent_messages.assert_called_once()
        mock_generate_embedding.assert_called_once()
        assert mock_client.notes_embedding == [0.1] * 1536 