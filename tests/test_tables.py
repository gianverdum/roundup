# tests/test_tables.py
import os
import random
from datetime import datetime, timedelta
from typing import Generator, Optional

import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.database import Base, get_db
from src.main import app
from src.models.table import Table
from src.schemas.event import EventCreate
from src.schemas.table import TableCreate

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


def generate_data_table(event_id: int, quantity: Optional[int] = None, seats: Optional[int] = None) -> TableCreate:
    """Generate a unique table with optional specific number and seat count."""
    return TableCreate(
        event_id=event_id,
        quantity=quantity if quantity is not None else random.randint(2, 12),
        seats=seats if seats is not None else random.randint(2, 10),
    )


def test_table_creation_success(test_client: TestClient, db_session: Session) -> None:
    """Validates that multiple tables can be created and returned with the correct attributes."""
    # Arrange
    event = generate_unique_event()

    # Convert datetime fields in event to ISO format before sending
    event_data_dict = event.model_dump()
    for key, value in event_data_dict.items():
        if isinstance(value, datetime):
            event_data_dict[key] = value.isoformat()

    # Send event data as part of the POST request
    response_event = test_client.post("/api/events/", json=event_data_dict)
    assert response_event.status_code == 201
    event_data = response_event.json()

    table_data = generate_data_table(event_data["id"], event_data["tables_count"], event_data["max_seats_per_table"])

    # Convert datetime fields in table_data to ISO format (if needed)
    table_data_dict = table_data.model_dump()
    for key, value in table_data_dict.items():
        if isinstance(value, datetime):
            table_data_dict[key] = value.isoformat()

    # Act
    response = test_client.post("/api/tables/", json=table_data_dict)

    # Assert
    assert response.status_code == 201
    response_data = response.json()

    # Assert the structure of the response
    assert isinstance(response_data, list)
    assert len(response_data) == table_data.quantity

    # Check each table in the response
    for table in response_data:
        assert table["table_number"] > 0
        assert table["seats"] == table_data.seats
        assert table["event_id"] == event_data["id"]
        assert "id" in table and isinstance(table["id"], int) and table["id"] > 0


def test_table_creation_with_missing_fields(test_client: TestClient, db_session: Session) -> None:
    """Tests that missing fields result in a 422 error response with appropriate error messages."""
    # Arrange
    event = generate_unique_event()

    # Convert datetime fields in event model to ISO format before sending
    event_data_dict = event.model_dump()
    for key, value in event_data_dict.items():
        if isinstance(value, datetime):
            event_data_dict[key] = value.isoformat()

    response_event = test_client.post("/api/events/", json=event_data_dict)
    assert response_event.status_code == 201
    event_data = response_event.json()

    # Convert datetime fields in event_data (from response) to ISO format before using them
    for key, value in event_data.items():
        if isinstance(value, datetime):
            event_data[key] = value.isoformat()

    # Missing the 'seats' field
    table_data = {
        "event_id": event_data["id"],  # Adjust to use the correct key after datetime conversion
        "number": 5,
    }

    # Act
    response = test_client.post("/api/tables/", json=table_data)

    # Assert
    assert response.status_code == 422
    response_data = response.json()
    assert "detail" in response_data
    assert isinstance(response_data["detail"], list)

    # Check for the error related to the missing 'seats' field
    missing_field_error = next((error for error in response_data["detail"] if error["loc"] == ["body", "seats"]), None)
    assert missing_field_error is not None
    assert missing_field_error["msg"] == "Field required"


def test_table_creation_with_invalid_data(test_client: TestClient, db_session: Session) -> None:
    """
    Tests that invalid table data (non-integer values such as strings, booleans, None)
    returns a 422 error with detailed error messages.
    """
    # Arrange
    event = generate_unique_event()

    # Convert datetime fields in event model to ISO format before sending
    event_data_dict = event.model_dump()
    for key, value in event_data_dict.items():
        if isinstance(value, datetime):
            event_data_dict[key] = value.isoformat()

    # Send request to create the event
    response_event = test_client.post("/api/events/", json=event_data_dict)
    assert response_event.status_code == 201
    event_data = response_event.json()

    # Prepare invalid table data with various non-integer values
    invalid_table_data = [
        {"event_id": event_data["id"], "seats": "invalid", "quantity": "invalid"},  # Strings
        {"event_id": event_data["id"], "seats": None, "quantity": None},  # None values
        {"event_id": event_data["id"], "seats": True, "quantity": False},  # Booleans
        {"event_id": event_data["id"], "seats": 3.5, "quantity": 5.5},  # Floats
    ]

    # Act & Assert: Check all invalid cases
    for invalid_data in invalid_table_data:
        response = test_client.post("/api/tables/", json=invalid_data)
        assert response.status_code == 422
        response_data = response.json()

        # Check that the error response contains details for the invalid data
        assert "detail" in response_data
        assert len(response_data["detail"]) > 0


def test_table_repr() -> None:
    """Validates the string representation of a Table instance."""
    # Arrange
    table = Table(
        id=1,
        event_id=2,
        table_number=1,
        seats=8,
    )

    # Act
    repr_output = repr(table)

    # Expected output string
    expected_output = (
        f"<Table id={table.id} event_id={table.event_id} " f"table_number={table.table_number} seats={table.seats}>"
    )

    # Assert
    assert repr_output == expected_output
