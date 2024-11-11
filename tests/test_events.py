# tests/test_events.py
import os
import random
from datetime import datetime, timedelta
from typing import Generator

import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from src.database import Base, get_db
from src.main import app
from src.models.event import Event
from src.schemas.event import EventCreate

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
    Base.metadata.drop_all(bind=engine)
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


# SQLAlchemyError mock definition
class MockSQLAlchemyError(SQLAlchemyError):
    pass


def generate_unique_event() -> EventCreate:
    """Generate a unique event with random data."""
    date = datetime.now() + timedelta(days=random.randint(1, 30))
    return EventCreate(
        name=f"Event {random.randint(1, 10000)}",
        date=date,
        location=f"Location {random.randint(1, 100)}",
        address=f"{random.randint(1, 1000)} - Sample Address, São Paulo - SP, 01310-{random.randint(100, 999)}",
        participant_limit=random.randint(10, 100),
        max_seats_per_table=random.randint(2, 8),
        tables_count=random.randint(1, 20),
    )


def create_event(test_client: TestClient) -> int:
    """Helper function to create an event and return the event_id."""
    event_data = generate_unique_event()
    event_data_dict = event_data.model_dump()
    event_data_dict["date"] = event_data.date.isoformat()

    response = test_client.post("/api/events/", json=event_data_dict)
    assert response.status_code == 201
    return response.json()["id"]


# Tests for POST /api/events/
def test_event_creation_success(test_client: TestClient, db_session: Session) -> None:
    """Test successful creation of an event."""
    # Arrange
    event_data = generate_unique_event()
    event_data_dict = event_data.model_dump()
    event_data_dict["date"] = event_data.date.isoformat()

    # Act
    response = test_client.post("/api/events/", json=event_data_dict)

    # Assert
    assert response.status_code == 201
    response_data = response.json()
    assert response_data["name"] == event_data.name


def test_event_creation_with_past_date(test_client: TestClient, db_session: Session) -> None:
    """Test that an event cannot be created with a past date."""
    # Arrange
    event_data = generate_unique_event()
    past_date = datetime.now() - timedelta(days=1)
    event_data.date = past_date
    event_data_dict = event_data.model_dump()
    event_data_dict["date"] = past_date.isoformat()

    # Act
    response = test_client.post("/api/events/", json=event_data_dict)

    # Assert
    assert response.status_code == 422
    response_data = response.json()
    assert response_data["detail"][0]["msg"] == "Value error, The event date cannot be in the past."


# Tests for GET /api/events/
def test_get_all_events_success(test_client: TestClient, db_session: Session) -> None:
    """Test retrieval of all events."""
    # Arrange
    create_event(test_client)

    # Act
    response = test_client.get("/api/events/")

    # Assert
    assert response.status_code == 200
    response_data = response.json()
    assert isinstance(response_data["items"], list)
    assert response_data["total_items"] >= 1


# Tests for GET /api/events/filter
def test_filter_events(test_client: TestClient, db_session: Session) -> None:
    """Test event filtering based on criteria."""
    # Arrange
    create_event(test_client)

    # Act
    response = test_client.get("/api/events/filter?name=Event")

    # Assert
    assert response.status_code == 200
    response_data = response.json()
    assert isinstance(response_data["items"], list)
    assert len(response_data["items"]) >= 1


# Tests for GET /api/events/{event_id}
def test_get_event_by_id_success(test_client: TestClient, db_session: Session) -> None:
    """Test retrieval of an event by ID."""
    # Arrange
    event_id = create_event(test_client)

    # Act
    response = test_client.get(f"/api/events/{event_id}")

    # Assert
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["id"] == event_id


def test_get_event_by_id_not_found(test_client: TestClient, db_session: Session) -> None:
    """Test retrieval of a non-existent event returns 404."""
    # Arrange/Act
    response = test_client.get("/api/events/9999")

    # Assert
    assert response.status_code == 404


# Tests for PUT /api/events/{event_id}
def test_update_event_success(test_client: TestClient, db_session: Session) -> None:
    """Test successful update of an event."""
    # Arrange
    event_id = create_event(test_client)
    updated_data = {
        "name": "Updated Event",
        "date": (datetime.now() + timedelta(days=15)).isoformat(),
        "location": "Updated Location",
        "address": "New Address, SP, 12345-678",
        "participant_limit": 60,
        "max_seats_per_table": 10,
        "tables_count": 5,
    }

    # Act
    response = test_client.put(f"/api/events/{event_id}", json=updated_data)

    # Assert
    assert response.status_code == 200


def test_update_event_not_found(test_client: TestClient, db_session: Session) -> None:
    """Test updating a non-existent event returns 404."""
    # Arrange
    updated_data = {
        "name": "Non-existent Event",
        "date": (datetime.now() + timedelta(days=15)).isoformat(),
        "location": "Nowhere",
        "address": "Non-existent Address",
        "participant_limit": 50,
        "max_seats_per_table": 8,
        "tables_count": 4,
    }

    # Act
    response = test_client.put("/api/events/9999", json=updated_data)

    # Assert
    assert response.status_code == 404


# Tests for DELETE /api/events/{event_id}
def test_delete_event_success(test_client: TestClient, db_session: Session) -> None:
    """Test successful deletion of an event by ID."""
    # Arrange
    event_id = create_event(test_client)

    # Act
    response = test_client.delete(f"/api/events/{event_id}")

    # Assert
    assert response.status_code == 204
    response = test_client.get(f"/api/events/{event_id}")
    assert response.status_code == 404


def test_delete_event_not_found(test_client: TestClient, db_session: Session) -> None:
    """Test deletion of a non-existent event returns 404."""
    # Arrange/Act
    response = test_client.delete("/api/events/9999")

    # Assert
    assert response.status_code == 404


# Additional tests
def test_event_repr() -> None:
    """Test string representation of an Event instance."""
    # Arrange
    event_data = generate_unique_event()
    event = Event(
        name=event_data.name,
        date=event_data.date,
        location=event_data.location,
        address=event_data.address,
        max_seats_per_table=event_data.max_seats_per_table,
        tables_count=event_data.tables_count,
    )

    # Act
    repr_output = repr(event)

    # Assert
    expected_output = (
        f"<Event(name={event_data.name!r}, "
        f"date={event_data.date}, "
        f"location={event_data.location!r}, "
        f"address={event_data.address!r}, "
        f"max_seats_per_table={event_data.max_seats_per_table}, "
        f"tables_count={event_data.tables_count})>"
    )

    assert repr_output == expected_output
