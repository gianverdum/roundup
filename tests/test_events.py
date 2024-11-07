# tests/test_events.py
import os
import random
from datetime import datetime, timedelta
from typing import Generator

import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError, SQLAlchemyError
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


def test_event_creation_success(test_client: TestClient, db_session: Session) -> None:
    """Validates that a new event can be added successfully via POST request."""
    # Arrange
    event_data = generate_unique_event()

    # Convert any datetime fields to ISO format (if necessary)
    event_data_dict = event_data.model_dump()
    for key, value in event_data_dict.items():
        if isinstance(value, datetime):
            event_data_dict[key] = value.isoformat()

    # Act
    response = test_client.post("/api/events/", json=event_data_dict)

    # Assert
    assert response.status_code == 201
    response_data = response.json()
    assert response_data["name"] == event_data.name
    assert response_data["location"] == event_data.location
    assert response_data["date"] == event_data.date.isoformat()
    assert "id" in response_data and isinstance(response_data["id"], int) and response_data["id"] > 0
    assert response_data["max_seats_per_table"] == event_data.max_seats_per_table
    assert response_data["tables_count"] == event_data.tables_count


def test_event_creation_with_past_date(test_client: TestClient, db_session: Session) -> None:
    """Validates that an event cannot be created with a past date."""
    # Arrange
    event_data = generate_unique_event()
    past_date = datetime.now() - timedelta(days=1)
    event_data.date = past_date  # Keep as a datetime object for type consistency

    # Act
    # Convert the date to ISO format string just before sending the request
    response = test_client.post(
        "/api/events/",
        json={
            **event_data.model_dump(),  # include all other fields
            "date": past_date.isoformat(),  # override the date with the string format
        },
    )

    # Assert
    assert response.status_code == 422
    response_data = response.json()
    assert len(response_data["detail"]) == 1
    assert response_data["detail"][0]["msg"] == "Value error, The event date cannot be in the past."
    assert response_data["detail"][0]["loc"] == ["body", "date"]


def test_event_repr() -> None:
    """Validates the string representation of an Event instance."""
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

    expected_output = (
        f"<Event(name={event_data.name!r}, "
        f"date={event_data.date}, "
        f"location={event_data.location!r}, "
        f"address={event_data.address!r}, "
        f"max_seats_per_table={event_data.max_seats_per_table}, "
        f"tables_count={event_data.tables_count})>"
    )

    # Assert
    assert repr_output == expected_output


def test_create_event_with_invalid_data(test_client: TestClient, db_session: Session) -> None:
    """Tests the creation of an event with invalid data."""
    invalid_event_data = {
        "name": "",
        "date": "invalid-date",
        "location": "Location",
        "address": "Address",
        "max_seats_per_table": 1,
        "tables_count": 0,
    }

    response = test_client.post("/api/events/", json=invalid_event_data)

    assert response.status_code == 422
    response_data = response.json()

    assert len(response_data["detail"]) > 0
    assert all("msg" in error for error in response_data["detail"])

    name_error = next((error for error in response_data["detail"] if error["loc"] == ["body", "name"]), None)
    date_error = next((error for error in response_data["detail"] if error["loc"] == ["body", "date"]), None)
    max_seats_error = next(
        (error for error in response_data["detail"] if error["loc"] == ["body", "max_seats_per_table"]), None
    )
    tables_count_error = next(
        (error for error in response_data["detail"] if error["loc"] == ["body", "tables_count"]), None
    )

    assert name_error is not None
    assert "msg" in name_error
    assert name_error["msg"] == "String should have at least 3 characters"

    assert date_error is not None
    assert "msg" in date_error
    assert "Input should be a valid datetime or date" in date_error["msg"]

    assert max_seats_error is not None
    assert "msg" in max_seats_error
    assert max_seats_error["msg"] == "Input should be greater than 1"

    assert tables_count_error is not None
    assert "msg" in tables_count_error
    assert tables_count_error["msg"] == "Input should be greater than 0"


def test_get_db(db_session: Session) -> None:
    """Tests that the get_db function returns a session."""
    # Act
    db = next(get_db())

    # Assert
    assert isinstance(db, Session)
    db.close()  # Ensure it closes without issue


def test_db_error_handler(test_client: TestClient) -> None:
    """Tests the db_error_handler middleware for OperationalError."""

    # Arrange: create a mock request that causes an OperationalError
    @app.get("/error")
    async def error_route() -> None:
        raise OperationalError("Mock Operational Error", "Some params", "Some connection")

    # Act
    response = test_client.get("/error")

    # Assert
    assert response.status_code == 500
    assert response.json() == {"detail": "Database error: Some connection"}


def test_read_root(test_client: TestClient) -> None:
    """Tests the read_root endpoint."""
    # Act
    response = test_client.get("/")

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the RoundUp API!"}


def test_db_error_handler_operational_error(test_client: TestClient) -> None:
    """Tests the db_error_handler middleware for OperationalError."""

    # Arrange
    @app.get("/mock-op-error")
    async def mock_operational_error() -> None:
        raise OperationalError("Mock Operational Error", "Some params", "Some connection")

    # Act
    response = test_client.get("/mock-op-error")

    # Assert
    assert response.status_code == 500
    assert response.json() == {"detail": "Database error: Some connection"}


def test_db_error_handler_sqlalchemy_error(test_client: TestClient) -> None:
    """Tests the db_error_handler middleware for SQLAlchemyError."""

    # Arrange
    @app.get("/mock-sql-error")
    async def mock_sqlalchemy_error() -> None:
        raise MockSQLAlchemyError("Mock SQLAlchemy Error")

    # Act
    response = test_client.get("/mock-sql-error")

    # Assert
    assert response.status_code == 500
    assert response.json() == {"detail": "Unexpected database error: Mock SQLAlchemy Error"}


def test_db_error_handler_unexpected_error(test_client: TestClient) -> None:
    """Tests the db_error_handler middleware for unexpected errors."""

    # Arrange
    @app.get("/mock-unexpected-error")
    async def mock_unexpected_error() -> None:
        raise ValueError("This is a mock unexpected error.")

    # Act
    response = test_client.get("/mock-unexpected-error")

    # Assert
    assert response.status_code == 500
    assert response.json() == {"detail": "An unexpected error occurred"}


def test_create_event_with_invalid_date_format(test_client: TestClient) -> None:
    """Tests creation of an event with an invalid date format."""
    # Arrange
    invalid_event_data = {
        "name": "Valid Event",
        "date": "invalid-date-format",
        "location": "Some Location",
        "address": "123 Sample Address",
        "participant_limit": 50,
        "max_seats_per_table": 0,
        "tables_count": 0,
    }

    # Act
    response = test_client.post("/api/events/", json=invalid_event_data)

    # Assert
    assert response.status_code == 422
    response_data = response.json()

    # Assert the structure of the error response
    assert "detail" in response_data
    assert isinstance(response_data["detail"], list)

    # Check for the specific error related to the date field
    date_error = next((error for error in response_data["detail"] if error["loc"] == ["body", "date"]), None)
    assert date_error is not None
    assert "msg" in date_error
    assert "invalid character in year" in date_error["msg"]

    # Check for the specific error related to the max_seats_per_table field
    max_seats_error = next(
        (error for error in response_data["detail"] if error["loc"] == ["body", "max_seats_per_table"]), None
    )
    assert max_seats_error is not None
    assert "msg" in max_seats_error
    assert max_seats_error["msg"] == "Input should be greater than 1"

    # Check for the specific error related to the tables_count field
    tables_count_error = next(
        (error for error in response_data["detail"] if error["loc"] == ["body", "tables_count"]), None
    )
    assert tables_count_error is not None
    assert "msg" in tables_count_error
    assert tables_count_error["msg"] == "Input should be greater than 0"


def test_create_event_with_missing_fields(test_client: TestClient) -> None:
    """Tests the creation of an event with missing fields."""
    # Arrange
    event_data = {
        "name": "Event without date",
        "location": "Some Location",
        # Missing date, address, participant_limit, max_seats_per_table, and tables_count
    }

    # Act
    response = test_client.post("/api/events/", json=event_data)

    # Assert
    assert response.status_code == 422
    response_data = response.json()

    # Assert the structure of the error response
    assert "detail" in response_data
    assert isinstance(response_data["detail"], list)

    # Check for the specific errors related to missing fields
    missing_fields_errors = [
        error
        for error in response_data["detail"]
        if error["loc"]
        in [
            ["body", "date"],
            ["body", "address"],
            ["body", "participant_limit"],
            ["body", "max_seats_per_table"],
            ["body", "tables_count"],
        ]
    ]
    assert len(missing_fields_errors) > 0

    # Check for the correct error message structure
    assert all(error["msg"] == "Field required" for error in missing_fields_errors)  # Ensure "Field required" message
