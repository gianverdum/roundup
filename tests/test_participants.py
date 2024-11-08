import os
import random
from datetime import datetime, timedelta
from typing import Generator

import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient
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

    # Example custom data that can vary per participant
    custom_data = {
        "membership_level": random.choice(["Silver", "Gold", "Platinum"]),
        "preferences": random.choice(["Vegetarian", "Non-Vegetarian", "Vegan"]),
        "registration_time": random.randint(1000000000, 9999999999),
    }

    # Generate full name with at least a first and last name
    first_name = f"Participant{random.randint(1, 10000)}"
    last_name = random.choice(["Smith", "Johnson", "Williams", "Brown", "Jones"])
    full_name = f"{first_name} {last_name}"

    # Generate WhatsApp number with at least 11 digits
    whatsapp = f"+5511{random.randint(100000000, 999999999)}"

    # Generate email in the correct format
    email = f"participant{random.randint(1, 10000)}@example.com"

    # Create and return the participant
    return ParticipantCreate(
        full_name=full_name,
        company_name=f"Company {random.randint(1, 100)}",
        whatsapp=whatsapp,
        email=email,
        event_id=event_id,
        custom_data=custom_data,
    )


def test_participant_creation_success(test_client: TestClient, db_session: Session) -> None:
    """Test that a participant can be successfully created."""
    # Arrange
    event_data = generate_unique_event()

    # Convert datetime fields in event to ISO format before sending
    event_data_dict = event_data.model_dump()
    for key, value in event_data_dict.items():
        if isinstance(value, datetime):
            event_data_dict[key] = value.isoformat()

    response = test_client.post("/api/events/", json=event_data_dict)
    assert response.status_code == 201
    event_id = response.json()["id"]

    participant_data = generate_unique_participant(event_id)

    # Act
    response = test_client.post("/api/participants/", json=participant_data.model_dump())

    # Assert
    assert response.status_code == 201
    response_data = response.json()
    assert response_data["full_name"] == participant_data.full_name
    assert response_data["company_name"] == participant_data.company_name
    assert response_data["whatsapp"] == participant_data.whatsapp
    assert response_data["email"] == participant_data.email
    assert response_data["event_id"] == participant_data.event_id
    assert "id" in response_data and isinstance(response_data["id"], int) and response_data["id"] > 0
    assert "custom_data" in response_data


def test_participant_creation_with_missing_fields(test_client: TestClient, db_session: Session) -> None:
    """Test that missing required fields result in a 422 error."""
    # Arrange
    event_data = generate_unique_event()

    # Convert datetime fields in event to ISO format before sending
    event_data_dict = event_data.model_dump()
    for key, value in event_data_dict.items():
        if isinstance(value, datetime):
            event_data_dict[key] = value.isoformat()

    response = test_client.post("/api/events/", json=event_data_dict)
    assert response.status_code == 201
    event_id = response.json()["id"]

    participant_data = {
        "full_name": "Missing Company",  # Missing other required fields
        "whatsapp": "+5511999999999",
        "email": "missingcompany@example.com",
        "event_id": event_id,
        # custom_data is missing
    }

    # Act
    response = test_client.post("/api/participants/", json=participant_data)

    # Assert
    assert response.status_code == 422
    response_data = response.json()
    assert "detail" in response_data
    assert isinstance(response_data["detail"], list)

    # Check for missing fields in the error response
    missing_field_error = next(
        (error for error in response_data["detail"] if error["loc"] == ["body", "company_name"]), None
    )
    assert missing_field_error is not None
    assert missing_field_error["msg"] == "Field required"


def create_event(test_client: TestClient) -> int:
    """Helper function to create an event and return the event_id."""
    event_data = generate_unique_event()
    # Convert datetime fields in event to ISO format before sending
    event_data_dict = event_data.model_dump()
    for key, value in event_data_dict.items():
        if isinstance(value, datetime):
            event_data_dict[key] = value.isoformat()

    response = test_client.post("/api/events/", json=event_data_dict)
    assert response.status_code == 201
    return response.json()["id"]


def test_participant_creation_with_invalid_whatsapp(test_client: TestClient, db_session: Session) -> None:
    """Test that invalid whatsapp format results in a 422 error."""
    event_id = create_event(test_client)

    invalid_data = {
        "full_name": "Invalid Data",
        "company_name": "Test Co",
        "whatsapp": "invalid",  # Invalid format
        "email": "validemail@example.com",
        "event_id": event_id,
        "custom_data": {"key": "value"},
    }

    response = test_client.post("/api/participants/", json=invalid_data)
    print(response.json())  # Print the response for debugging
    assert response.status_code == 422
    response_data = response.json()
    assert "detail" in response_data
    assert len(response_data["detail"]) > 0


def test_participant_creation_with_invalid_email(test_client: TestClient, db_session: Session) -> None:
    """Test that invalid email format results in a 422 error."""
    event_id = create_event(test_client)

    invalid_data = {
        "full_name": "Invalid Email",
        "company_name": "Test Co",
        "whatsapp": "+5511999999999",
        "email": "invalid@",  # Invalid email format
        "event_id": event_id,
        "custom_data": {"key": "value"},
    }

    response = test_client.post("/api/participants/", json=invalid_data)
    print(response.json())  # Print the response for debugging
    assert response.status_code == 422
    response_data = response.json()
    assert "detail" in response_data
    assert len(response_data["detail"]) > 0


def test_participant_creation_with_missing_last_name(test_client: TestClient, db_session: Session) -> None:
    """Test that missing last name in full_name results in a 422 error."""
    event_id = create_event(test_client)

    invalid_data = {
        "full_name": "John",  # Only a first name
        "company_name": "Test Co",
        "whatsapp": "+5511999999999",
        "email": "valid@example.com",
        "event_id": event_id,
        "custom_data": {"key": "value"},
    }

    response = test_client.post("/api/participants/", json=invalid_data)
    print(response.json())  # Print the response for debugging
    assert response.status_code == 422
    response_data = response.json()
    assert "detail" in response_data
    assert len(response_data["detail"]) > 0


def test_participant_creation_with_invalid_full_name_type(test_client: TestClient, db_session: Session) -> None:
    """Test that invalid type for full_name results in a 422 error."""
    event_id = create_event(test_client)

    invalid_data = {
        "full_name": 123,  # Invalid type (numeric instead of string)
        "company_name": "Test Co",
        "whatsapp": "+5511999999999",
        "email": "valid@data.com",
        "event_id": event_id,
        "custom_data": {"key": "value"},
    }

    response = test_client.post("/api/participants/", json=invalid_data)
    print(response.json())  # Print the response for debugging
    assert response.status_code == 422
    response_data = response.json()
    assert "detail" in response_data
    assert len(response_data["detail"]) > 0


def test_participant_creation_with_invalid_custom_data_format(test_client: TestClient, db_session: Session) -> None:
    """Test that invalid custom_data format results in a 422 error."""
    event_id = create_event(test_client)

    invalid_data = {
        "full_name": "Custom Data Invalid",
        "company_name": "Test Co",
        "whatsapp": "+5511999999999",
        "email": "valid@custom.com",
        "event_id": event_id,
        "custom_data": "invalid_string_instead_of_json",  # Invalid format
    }

    response = test_client.post("/api/participants/", json=invalid_data)
    print(response.json())  # Print the response for debugging
    assert response.status_code == 422
    response_data = response.json()
    assert "detail" in response_data
    assert len(response_data["detail"]) > 0


def test_participant_repr() -> None:
    """Test the string representation of the Participant instance."""
    # Arrange
    participant = Participant(
        id=1,
        full_name="John Doe",
        company_name="Tech Corp",
        whatsapp="+5511999999999",
        email="john.doe@example.com",
        event_id=1,
        custom_data={"preferences": {"theme": "dark", "notifications": True}, "referral": "marketing_campaign_A"},
    )

    # Act
    repr_output = repr(participant)

    # Expected output string, ensure the correct representation
    expected_output = (
        f"<Participant(id={participant.id}), "
        f"full_name={participant.full_name!r}, "
        f"company_name={participant.company_name!r}, "
        f"whatsapp={participant.whatsapp!r}, "
        f"email={participant.email!r}, "
        f"event_id={participant.event_id}, "
        f"custom_data={participant.custom_data!r})>"
    )

    # Assert
    assert repr_output == expected_output
