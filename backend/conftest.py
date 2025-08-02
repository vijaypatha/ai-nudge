# FILE: backend/conftest.py


import pytest
from typing import Generator
import uuid
from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool
from unittest.mock import patch

# Patches to silence noisy startup functions
lifespan_patches = [
    patch('api.main.semantic_service.initialize_vector_index', return_value=None)
]

# App import and DB setup
from api.main import app
from api.security import get_current_user_from_token
from data.database import get_session
from data.models.user import User

# Test database engine setup
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# --- NEW: This fixture ensures all modules use the same test engine ---
@pytest.fixture(scope='session', autouse=True)
def patch_db_engine():
    """
    Patches the engine used by service modules to ensure they use the
    test database engine for all operations. This is critical for
    integration tests that call service-layer code directly.
    """
    # We patch the engine in any module that might import it directly
    with patch('data.crm.engine', new=engine), \
         patch('data.database.engine', new=engine):
        yield

@pytest.fixture(name="session", scope="function")
def session_fixture() -> Generator[Session, None, None]:
    """Creates a new, empty database session for each test."""
    for p in lifespan_patches:
        p.start()
    
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)

    for p in lifespan_patches:
        p.stop()

@pytest.fixture
def test_user(session: Session) -> User:
    """Creates a test user and saves it to the in-memory test database."""
    user = User(
        id=uuid.UUID("a8c6f1d7-8f7a-4b6e-8b0f-9e5a7d6c5b4a"),
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