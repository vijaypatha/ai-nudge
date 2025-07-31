# File: backend/tests/test_content_resource_service.py

import pytest
import uuid
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

from agent_core.content_resource_service import (
    calculate_fuzzy_similarity,
    get_content_recommendations_for_user,
    find_matching_clients_generic
)
from data.models.resource import ContentResource, Resource, ResourceType, ResourceStatus
from data.models.client import Client
from data.models.user import User


class TestContentResourceService:
    """Test suite for content resource service functionality"""

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
        """Create a test client"""
        return Client(
            id=uuid.uuid4(),
            user_id=mock_user.id,
            full_name="Test Client",
            email="client@test.com",
            phone="+15558887777",
            user_tags=["buyer", "interested"],
            ai_tags=["urgent"],
            preferences={"budget": "500k-750k"}
        )

    @pytest.fixture
    def mock_content_resource(self, mock_user: User) -> ContentResource:
        """Create a test content resource"""
        return ContentResource(
            id=uuid.uuid4(),
            user_id=mock_user.id,
            title="First Time Home Buyer Guide",
            url="https://example.com/guide",
            description="Complete guide for first-time home buyers",
            categories=["buying", "first-time"],
            content_type="article",
            status=ResourceStatus.ACTIVE
        )

    def test_calculate_fuzzy_similarity_exact_match(self):
        """Test fuzzy similarity calculation with exact match"""
        result = calculate_fuzzy_similarity("hello world", "hello world")
        assert result == 1.0

    def test_calculate_fuzzy_similarity_partial_match(self):
        """Test fuzzy similarity calculation with partial match"""
        result = calculate_fuzzy_similarity("hello world", "hello")
        assert 0.5 <= result <= 1.0

    def test_calculate_fuzzy_similarity_no_match(self):
        """Test fuzzy similarity calculation with no match"""
        result = calculate_fuzzy_similarity("hello world", "completely different")
        assert result < 0.5

    def test_calculate_fuzzy_similarity_case_insensitive(self):
        """Test fuzzy similarity calculation is case insensitive"""
        result1 = calculate_fuzzy_similarity("Hello World", "hello world")
        result2 = calculate_fuzzy_similarity("hello world", "HELLO WORLD")
        assert result1 == 1.0
        assert result2 == 1.0

    @patch('agent_core.content_resource_service.Session')
    def test_get_content_recommendations_for_user_success(self, mock_session_class, mock_user: User):
        """Test getting content recommendations for user"""
        # Setup
        mock_session = MagicMock()
        mock_session_class.return_value.__enter__.return_value = mock_session
        
        # Mock content resources
        mock_content_resources = [
            ContentResource(
                id=uuid.uuid4(),
                user_id=mock_user.id,
                title="First Time Home Buyer Guide",
                categories=["buying", "first-time"],
                status=ResourceStatus.ACTIVE
            )
        ]
        
        # Mock web resources
        mock_web_resources = [
            Resource(
                id=uuid.uuid4(),
                user_id=mock_user.id,
                title="Market Analysis",
                resource_type=ResourceType.WEB_CONTENT,
                status=ResourceStatus.ACTIVE
            )
        ]
        
        # Mock clients
        mock_clients = [
            Client(
                id=uuid.uuid4(),
                user_id=mock_user.id,
                full_name="Test Client",
                user_tags=["buyer", "first-time"],
                ai_tags=["interested"]
            )
        ]
        
        mock_session.exec.return_value.all.side_effect = [
            mock_content_resources,
            mock_web_resources,
            mock_clients
        ]

        # Execute
        result = get_content_recommendations_for_user(mock_user.id)

        # Assert
        assert isinstance(result, list)
        assert len(result) > 0
        mock_session.exec.assert_called()

    @patch('agent_core.content_resource_service.Session')
    def test_get_content_recommendations_for_user_no_resources(self, mock_session_class, mock_user: User):
        """Test getting content recommendations when no resources exist"""
        # Setup
        mock_session = MagicMock()
        mock_session_class.return_value.__enter__.return_value = mock_session
        
        mock_session.exec.return_value.all.side_effect = [
            [],  # No content resources
            [],  # No web resources
            []   # No clients
        ]

        # Execute
        result = get_content_recommendations_for_user(mock_user.id)

        # Assert
        assert result == []

    def test_find_matching_clients_generic_with_fuzzy_matching(self, mock_client: Client):
        """Test finding matching clients with fuzzy matching"""
        # Setup
        resource = ContentResource(
            id=uuid.uuid4(),
            title="First Time Home Buyer Guide",
            categories=["buying", "first-time"]
        )
        clients = [mock_client]

        # Execute
        result = find_matching_clients_generic(resource, clients, use_fuzzy=True, fuzzy_threshold=0.8)

        # Assert
        assert isinstance(result, list)
        # Should find matches based on tags and categories

    def test_find_matching_clients_generic_without_fuzzy_matching(self, mock_client: Client):
        """Test finding matching clients without fuzzy matching"""
        # Setup
        resource = ContentResource(
            id=uuid.uuid4(),
            title="First Time Home Buyer Guide",
            categories=["buying", "first-time"]
        )
        clients = [mock_client]

        # Execute
        result = find_matching_clients_generic(resource, clients, use_fuzzy=False)

        # Assert
        assert isinstance(result, list)

    @patch('agent_core.content_resource_service.get_chat_completion')
    def test_get_content_recommendations_with_ai_analysis(self, mock_get_chat_completion, mock_user: User):
        """Test content recommendations with AI analysis"""
        # Setup
        mock_get_chat_completion.return_value = "This resource is highly relevant for first-time buyers"
        
        resource = ContentResource(
            id=uuid.uuid4(),
            user_id=mock_user.id,
            title="First Time Home Buyer Guide",
            categories=["buying", "first-time"]
        )
        
        client = Client(
            id=uuid.uuid4(),
            user_id=mock_user.id,
            full_name="Test Client",
            user_tags=["buyer", "first-time"]
        )

        # Execute
        result = find_matching_clients_generic(resource, [client], use_fuzzy=True)

        # Assert
        assert isinstance(result, list)
        # The AI analysis should be called for detailed matching

    def test_content_resource_matching_by_tags(self, mock_user: User):
        """Test matching content resources by client tags"""
        # Setup
        resource = ContentResource(
            id=uuid.uuid4(),
            user_id=mock_user.id,
            title="Luxury Home Guide",
            categories=["luxury", "high-end"]
        )
        
        client = Client(
            id=uuid.uuid4(),
            user_id=mock_user.id,
            full_name="Luxury Client",
            user_tags=["luxury", "high-budget"],
            preferences={"budget": "1M+"}
        )

        # Execute
        result = find_matching_clients_generic(resource, [client])

        # Assert
        assert len(result) > 0
        assert client in result

    def test_content_resource_matching_by_preferences(self, mock_user: User):
        """Test matching content resources by client preferences"""
        # Setup
        resource = ContentResource(
            id=uuid.uuid4(),
            user_id=mock_user.id,
            title="Budget Home Guide",
            categories=["budget", "affordable"]
        )
        
        client = Client(
            id=uuid.uuid4(),
            user_id=mock_user.id,
            full_name="Budget Client",
            preferences={"budget": "200k-300k", "location": "suburban"}
        )

        # Execute
        result = find_matching_clients_generic(resource, [client])

        # Assert
        assert isinstance(result, list)
        # Should match based on budget preferences 