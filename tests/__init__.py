"""Tests package initialization."""

import pytest
import asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from database.models import Base
from database.connection import get_db
from app import app


# Test database URL - use a separate test database
TEST_DATABASE_URL = "postgresql://postgres:password@localhost:5432/ollama_api_test"

# Create test engine and session
test_engine = create_engine(TEST_DATABASE_URL)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestSessionLocal()
        yield db
    finally:
        db.close()


# Override the database dependency
app.dependency_overrides[get_db] = override_get_db

# Create test client
client = TestClient(app)


@pytest.fixture(scope="session")
def setup_test_db():
    """Setup test database."""
    # Create all tables
    Base.metadata.create_all(bind=test_engine)
    yield
    # Drop all tables after tests
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def test_client():
    """Get test client."""
    return client


@pytest.fixture
def test_db():
    """Get test database session."""
    return TestSessionLocal()