# FILE: backend/conftest.py


import pytest
from typing import Generator
import uuid
from datetime import datetime, timezone
import os

from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool
from unittest.mock import patch

# Patches to silence noisy startup functions
lifespan_patches = [
    patch('api.main.semantic_service.initialize_vector_index', return_value=None)
]

# Test database engine setup - USE ENVIRONMENT DATABASE IN CI
def get_test_engine():
    """Get the appropriate test database engine based on environment."""
    # Check if we're in CI (GitHub Actions)
    if os.getenv('GITHUB_ACTIONS') == 'true':
        # Use the actual database URL from environment in CI
        from data.database import engine
        return engine
    else:
        # Use SQLite for local development tests
        return create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )

# Initialize engine lazily to avoid import-time issues
_engine = None

def get_engine():
    """Get the test engine, initializing it if needed."""
    global _engine
    if _engine is None:
        _engine = get_test_engine()
    return _engine

# --- Import models to ensure they're registered ---
from data.models import (
    User, Client, Resource, ContentResource, Message, ScheduledMessage,
    CampaignBriefing, MarketEvent, PipelineRun, Faq, NegativePreference
)
from data.models.campaign import CampaignStatus

# App import and DB setup
from api.main import app
from api.security import get_current_user_from_token
from data.database import get_session
import data.database

# --- SIMPLIFIED: No complex patching needed in CI ---
@pytest.fixture(scope='session', autouse=True)
def setup_test_environment():
    """
    Sets up the test environment.
    """
    import os
    if os.getenv('GITHUB_ACTIONS') == 'true':
        print(f"Running tests in CI environment with PostgreSQL")
        import data.database
        data.database.engine = get_engine()
    else:
        print(f"Running tests in local environment with SQLite")
    yield

@pytest.fixture(name="session", scope="function")
def session_fixture() -> Generator[Session, None, None]:
    """
    Provides a clean database for every test.
    This fixture drops all tables and recreates them before each test,
    ensuring complete test isolation.
    """
    engine = get_engine()
    
    # Start with a clean slate for every test
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    
    with Session(engine) as session:
        yield session

@pytest.fixture
def test_user(session: Session) -> User:
    """Creates a test user and saves it to the database."""
    user = User(
        id=uuid.uuid4(),
        full_name="Test User",
        email="test@example.com",
        phone_number="+15551234567"
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

@pytest.fixture(name="client")
def client_fixture(session: Session) -> Generator[TestClient, None, None]:
    """Creates a TestClient that uses the clean test database."""
    def get_session_override() -> Generator[Session, None, None]:
        yield session
    
    app.dependency_overrides[get_session] = get_session_override
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()

@pytest.fixture
def authenticated_client(client: TestClient, test_user: User) -> Generator[TestClient, None, None]:
    """Provides an authenticated client by using FastAPI's dependency_overrides."""
    def get_current_user_override():
        return test_user

    app.dependency_overrides[get_current_user_from_token] = get_current_user_override
    client.headers["Authorization"] = "Bearer fake-test-token"
    yield client
    app.dependency_overrides.clear()

@pytest.fixture
def test_client(session: Session, test_user: User) -> Client:
    """Creates a test client linked to the test user."""
    client = Client(
        id=uuid.uuid4(),
        user_id=test_user.id,
        full_name="Test Client",
        phone_number="+15559876543"
    )
    session.add(client)
    session.commit()
    session.refresh(client)
    return client

@pytest.fixture
def test_campaign(session: Session, test_user: User) -> CampaignBriefing:
    """Creates a test campaign briefing linked to the test user."""
    briefing = CampaignBriefing(
        id=uuid.uuid4(),
        user_id=test_user.id,
        campaign_type="market_opportunity",
        headline="Test Campaign",
        original_draft="Test draft content",
        key_intel={"test": "data"},
        matched_audience=[],
        status=CampaignStatus.DRAFT
    )
    session.add(briefing)
    session.commit()
    session.refresh(briefing)
    return briefing

@pytest.fixture
def test_resource(session: Session, test_user: User) -> Resource:
    """Creates a test resource linked to the test user."""
    resource = Resource(
        id=uuid.uuid4(),
        user_id=test_user.id,
        resource_type="property",
        title="Test Property",
        attributes={"PublicRemarks": "Test property description"}
    )
    session.add(resource)
    session.commit()
    session.refresh(resource)
    return resource