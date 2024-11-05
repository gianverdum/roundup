# tests/test_events.py
import os
import random
from datetime import datetime, timedelta
from typing import Dict, Generator

import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.database import Base, get_db
from src.main import app

# Load the database URL from the .env file
load_dotenv()
DATABASE_URL = os.getenv("POSTGRES_URL")

# Adjust the DATABASE_URL for compatibility
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

if DATABASE_URL:
    DATABASE_URL = DATABASE_URL.split("&supa=")[0]

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in the environment variables")

# Set up the database engine
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """Create a new DB session for each test."""
    connection = engine.connect()
    transaction = connection.begin()

    session = SessionLocal(bind=connection)
    Base.metadata.create_all(bind=engine)

    yield session

    session.close()
    if transaction.is_active:
        transaction.rollback()
    connection.close()


@pytest.fixture
def test_client(db_session: Session) -> Generator[TestClient, None, None]:
    """Create a TestClient instance."""
    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app) as client:
        yield client


def generate_unique_event() -> Dict[str, str]:
    """Generate a unique event dictionary with random data."""
    return {
        "name": f"Event {random.randint(1, 10000)}",
        "date": (datetime.now() + timedelta(days=random.randint(1, 30))).isoformat(),
        "location": f"Location {random.randint(1, 100)}",
        "address": f"{random.randint(1, 1000)} - Sample Address, São Paulo - SP, 01310-{random.randint(100, 999)}",
        "participant_limit": str(random.randint(10, 100)),
    }


def test_event_creation_success(test_client: TestClient, db_session: Session) -> None:
    """Validates that a new event can be added successfully via POST request."""
    # Arrange
    event_data = generate_unique_event()

    # Act
    response = test_client.post("/api/events/", json=event_data)

    # Assert
    assert response.status_code == 201
    response_data = response.json()
    assert response_data["name"] == event_data["name"]
    assert response_data["location"] == event_data["location"]
    assert response_data["date"] == event_data["date"]
    assert "id" in response_data and isinstance(response_data["id"], int) and response_data["id"] > 0
