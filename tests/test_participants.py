# tests/test_participants.py
import os
import random
from datetime import datetime, timedelta
from typing import Generator

import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from pytest_mock import MockerFixture
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.database import Base, get_db
from src.main import app
from src.models.participant import Participant
from src.schemas.event import EventCreate
from src.schemas.participant import ParticipantCreate

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


def generate_unique_participant(event_id: int) -> ParticipantCreate:
    """Generate a unique participant with random data, including custom_data in JSON format."""
    custom_data = {
        "membership_level": random.choice(["Silver", "Gold", "Platinum"]),
        "preferences": random.choice(["Vegetarian", "Non-Vegetarian", "Vegan"]),
        "registration_time": random.randint(1000000000, 9999999999),
    }

    first_name = f"Participant{random.randint(1, 10000)}"
    last_name = random.choice(["Smith", "Johnson", "Williams", "Brown", "Jones"])
    full_name = f"{first_name} {last_name}"
    whatsapp = f"+5511{random.randint(100000000, 999999999)}"
    email = f"participant{random.randint(1, 10000)}@example.com"

    return ParticipantCreate(
        full_name=full_name,
        company_name=f"Company {random.randint(1, 100)}",
        whatsapp=whatsapp,
        email=email,
        event_id=event_id,
        custom_data=custom_data,
    )


def create_event(test_client: TestClient) -> int:
    """Helper function to create an event and return the event_id."""
    event_data = generate_unique_event()
    event_data_dict = event_data.model_dump()
    for key, value in event_data_dict.items():
        if isinstance(value, datetime):
            event_data_dict[key] = value.isoformat()

    response = test_client.post("/api/events/", json=event_data_dict)
    assert response.status_code == 201
    return response.json()["id"]


def create_participant(test_client: TestClient, event_id: int) -> int:
    """Helper function to create a participant and return the participant_id."""
    participant_data = generate_unique_participant(event_id)
    response = test_client.post("/api/participants/", json=participant_data.model_dump())
    assert response.status_code == 201
    return response.json()["id"]


# CRUD Tests for /api/participants/
def test_participant_creation_success(test_client: TestClient) -> None:
    """Test successful creation of a participant."""
    # Arrange
    event_id = create_event(test_client)
    participant_data = generate_unique_participant(event_id)

    # Act
    response = test_client.post("/api/participants/", json=participant_data.model_dump())

    # Assert
    assert response.status_code == 201
    response_data = response.json()
    assert response_data["full_name"] == participant_data.full_name
    assert response_data["company_name"] == participant_data.company_name
    assert response_data["is_present"] is False


def test_get_participant(test_client: TestClient) -> None:
    """Test retrieving a participant by ID."""
    # Arrange
    event_id = create_event(test_client)
    participant_id = create_participant(test_client, event_id)

    # Act
    response = test_client.get(f"/api/participants/{participant_id}")

    # Assert
    assert response.status_code == 200
    assert response.json()["id"] == participant_id


def test_get_participant_list(test_client: TestClient) -> None:
    """Test retrieving the list of all participants."""
    # Arrange
    event_id = create_event(test_client)
    create_participant(test_client, event_id)

    # Act
    response = test_client.get("/api/participants/")

    # Assert
    assert response.status_code == 200
    assert len(response.json()) > 0


def test_update_participant(test_client: TestClient) -> None:
    """Test updating a participant's details."""
    # Arrange
    event_id = create_event(test_client)
    participant_id = create_participant(test_client, event_id)
    updated_data = {
        "full_name": "Updated Name",
        "company_name": "Updated Company",
        "whatsapp": "+5511998888888",
        "email": "updated@example.com",
        "event_id": event_id,
        "custom_data": {"updated_key": "updated_value"},
    }

    # Act
    response = test_client.put(f"/api/participants/{participant_id}", json=updated_data)

    # Assert
    assert response.status_code == 200
    assert response.json()["full_name"] == updated_data["full_name"]


def test_delete_participant_success(test_client: TestClient, db_session: Session) -> None:
    """Test successful deletion of a participant by ID."""
    # Arrange
    event_id = create_event(test_client)  # Ensure the event exists
    participant_id = create_participant(test_client, event_id)  # Ensure the participant exists

    # Act
    response = test_client.delete(f"/api/participants/{participant_id}")

    # Assert
    assert response.status_code == 204

    response = test_client.get(f"/api/participants/{participant_id}")

    assert response.status_code == 404


def test_check_in_participant_success(test_client: TestClient) -> None:
    """Test successful check-in of a participant."""
    # Arrange
    event_id = create_event(test_client)
    participant_id = create_participant(test_client, event_id)

    # Act
    response = test_client.post(f"/api/participants/{participant_id}/check-in")

    # Assert
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["is_present"] is True
    assert response_data["id"] == participant_id


def test_check_in_participant_not_found(test_client: TestClient) -> None:
    """Test check-in for a non-existent participant returns 404."""
    # Act
    response = test_client.post("/api/participants/9999/check-in")

    # Assert
    assert response.status_code == 404
    response_data = response.json()
    assert response_data["detail"] == "Participant not found"


@pytest.mark.skip(reason="Complex setup; revisit in future.")
def test_check_in_participant_unexpected_error(mocker: MockerFixture, test_client: TestClient) -> None:
    """Test unexpected error during participant check-in."""
    # Arrange
    event_id = create_event(test_client)
    participant_id = create_participant(test_client, event_id)

    # Mock `db.commit` to raise an exception
    mocker.patch(
        "src.services.participant_service.check_in_participant", side_effect=Exception("Mocked unexpected error")
    )

    # Act
    response = test_client.post(f"/api/participants/{participant_id}/check-in")

    # Assert
    assert response.status_code == 500
    response_data = response.json()
    assert "An unexpected error occurred" in response_data["detail"]


# Additional test for __repr__ method
def test_participant_repr() -> None:
    """Test the string representation of a Participant instance."""
    # Arrange
    participant = Participant(
        id=1,
        full_name="John Doe",
        company_name="Tech Corp",
        whatsapp="+5511999999999",
        email="john.doe@example.com",
        event_id=1,
        custom_data={"preferences": {"theme": "dark", "notifications": True}, "referral": "campaign_A"},
        is_present=True,
    )

    # Act
    repr_output = repr(participant)

    # Assert
    expected_output = (
        f"<Participant(id={participant.id}), "
        f"full_name={participant.full_name!r}, "
        f"company_name={participant.company_name!r}, "
        f"whatsapp={participant.whatsapp!r}, "
        f"email={participant.email!r}, "
        f"event_id={participant.event_id}, "
        f"custom_data={participant.custom_data!r}, "
        f"is_present={participant.is_present})>"
    )
    assert repr_output == expected_output
