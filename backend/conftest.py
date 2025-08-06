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

engine = get_test_engine()

# --- CRITICAL FIX: Import models ONCE to prevent multiple registration ---
# Models are imported here to ensure they're registered only once
# with SQLModel.metadata before any test execution
from data.models import (
    User, Client, Resource, ContentResource, Message, ScheduledMessage,
    CampaignBriefing, MarketEvent, PipelineRun, Faq, NegativePreference
)

# App import and DB setup
from api.main import app
from api.security import get_current_user_from_token
from data.database import get_session
import data.database

# --- SIMPLIFIED: No complex patching needed in CI ---
@pytest.fixture(scope='session', autouse=True)
def setup_test_environment():
    """
    Sets up the test environment. In CI, we use the actual database.
    In local development, we use SQLite.
    """
    import os
    if os.getenv('GITHUB_ACTIONS') == 'true':
        print(f"Running tests in CI environment with PostgreSQL")
        # In CI, we need to patch the engine so that API code uses the same engine
        # that has the tables created by migrations
        import data.database
        data.database.engine = engine
    else:
        print(f"Running tests in local environment with SQLite")
    yield

@pytest.fixture(name="session", scope="function")
def session_fixture() -> Generator[Session, None, None]:
    """Creates a new, empty database session for each test."""
    for p in lifespan_patches:
        p.start()
    
    # Models are already imported at module level, so we don't need to re-import them
    
    # In CI, we use the actual database with migrations, so don't create/drop tables
    # In local development, we use SQLite and create/drop tables for each test
    import os
    if os.getenv('GITHUB_ACTIONS') != 'true':
        # Create all tables in the test database for local development
        SQLModel.metadata.create_all(engine)
    
    with Session(engine) as session:
        yield session
    
    # Only drop tables if not in CI (where we use migrations)
    if os.getenv('GITHUB_ACTIONS') != 'true':
        SQLModel.metadata.drop_all(engine)

    for p in lifespan_patches:
        p.stop()

@pytest.fixture
def test_user(session: Session) -> User:
    """Creates a test user and saves it to the in-memory test database."""
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
    """Creates a base TestClient that uses our isolated test database."""
    def get_session_override():
        return session
    
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