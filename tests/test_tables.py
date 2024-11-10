# tests/test_tables.py
import os
import random
from datetime import datetime
from typing import Any, Dict, Generator, Optional

import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.database import Base, get_db
from src.main import app
from src.models.table import Table
from src.schemas.table import TableCreate
from tests.test_events import generate_unique_event

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


def generate_data_table(event_id: int, quantity: Optional[int] = None, seats: Optional[int] = None) -> TableCreate:
    """Generate a table creation schema with event ID, quantity, and seat count."""
    return TableCreate(
        event_id=event_id,
        quantity=quantity if quantity is not None else random.randint(2, 12),
        seats=seats if seats is not None else random.randint(2, 10),
    )


def create_event_with_isoformat(test_client: TestClient) -> dict[str, Any]:
    """Helper function to create an event with ISO-formatted datetime fields."""
    event = generate_unique_event()
    event_data_dict = event.model_dump()
    for key, value in event_data_dict.items():
        if isinstance(value, datetime):
            event_data_dict[key] = value.isoformat()

    response = test_client.post("/api/events/", json=event_data_dict)
    assert response.status_code == 201, f"Failed to create event: {response.json()}"
    return response.json()


def create_table(
    test_client: TestClient, event_id: int, quantity: Optional[int] = None, seats: Optional[int] = None
) -> int:
    """Helper function to create tables and return the first created table_id."""
    table_data = generate_data_table(event_id=event_id, quantity=quantity, seats=seats)
    response = test_client.post("/api/tables/", json=table_data.model_dump())
    assert response.status_code == 201, f"Failed to create table: {response.json()}"
    return response.json()[0]["id"]


async def update_table(table_id: int, table_data: Dict[str, Any], db: Session) -> Optional[Dict[str, Any]]:
    """Update a table's information, checking for NoneType before updating."""
    table = db.query(Table).filter(Table.id == table_id).first()
    if not table:
        return None

    for key, value in table_data.items():
        setattr(table, key, value)
    db.commit()
    db.refresh(table)

    return {"id": table.id, "event_id": table.event_id, "table_number": table.table_number, "seats": table.seats}


# Tests for POST /api/tables/
def test_table_creation_success(test_client: TestClient) -> None:
    """Test successful creation of tables."""
    # Arrange
    event_data = create_event_with_isoformat(test_client)
    event_id = event_data["id"]
    max_seats = event_data["max_seats_per_table"]

    table_data = generate_data_table(event_id, quantity=3, seats=max_seats)

    # Act
    response = test_client.post("/api/tables/", json=table_data.model_dump())

    # Assert
    assert response.status_code == 201
    response_data = response.json()
    assert len(response_data) == 3
    assert all(table["seats"] == max_seats for table in response_data)


def test_table_creation_with_missing_fields(test_client: TestClient) -> None:
    """Test that missing fields result in a 422 error."""
    event_data = create_event_with_isoformat(test_client)
    event_id = event_data["id"]

    # Act
    response = test_client.post("/api/tables/", json={"event_id": event_id})

    # Assert
    assert response.status_code == 422


# Tests for GET /api/tables/
def test_get_all_tables_success(test_client: TestClient) -> None:
    """Test retrieval of all tables."""
    event_data = create_event_with_isoformat(test_client)
    event_id = event_data["id"]
    max_seats = event_data["max_seats_per_table"]

    create_table(test_client, event_id, seats=max_seats)

    response = test_client.get("/api/tables/")
    assert response.status_code == 200
    assert isinstance(response.json()["items"], list)


# Tests for GET /api/tables/filter
def test_filter_tables(test_client: TestClient) -> None:
    """Test filtering tables by specific criteria."""
    # Arrange
    event_data = create_event_with_isoformat(test_client)
    event_id = event_data["id"]
    max_seats = event_data["max_seats_per_table"]

    create_table(test_client, event_id, seats=max_seats)

    # Act
    response = test_client.get(f"/api/tables/filter?event_id={event_id}")

    # Assert
    assert response.status_code == 200
    response_data = response.json()
    assert isinstance(response_data["items"], list)
    assert len(response_data["items"]) >= 1


# Tests for GET /api/tables/{table_id}
def test_get_table_by_id_success(test_client: TestClient) -> None:
    """Test retrieval of a table by its ID."""
    event_data = create_event_with_isoformat(test_client)
    event_id = event_data["id"]
    max_seats = event_data["max_seats_per_table"]

    table_id = create_table(test_client, event_id, seats=max_seats)
    response = test_client.get(f"/api/tables/{table_id}")

    assert response.status_code == 200
    assert response.json()["id"] == table_id


def test_get_table_by_id_not_found(test_client: TestClient) -> None:
    """Test retrieval of a non-existent table returns 404."""
    # Act
    response = test_client.get("/api/tables/9999")

    # Assert
    assert response.status_code == 404


# Tests for PUT /api/tables/{table_id}
def test_update_table_success(test_client: TestClient) -> None:
    """Test successful update of a table."""
    # Criação do evento e da mesa
    event_data = create_event_with_isoformat(test_client)
    event_id = event_data["id"]
    max_seats = event_data["max_seats_per_table"]

    table_id = create_table(test_client, event_id, seats=max_seats)
    updated_data = {"event_id": event_id, "table_number": 2, "seats": max_seats}

    response = test_client.put(f"/api/tables/{table_id}", json=updated_data)

    assert response.status_code == 200, f"Unexpected error: {response.json()}"
    response_data = response.json()
    assert response_data["table_number"] == updated_data["table_number"]


def test_update_table_not_found(test_client: TestClient) -> None:
    """Test updating a non-existent table returns 404."""
    event_data = create_event_with_isoformat(test_client)
    event_id = event_data["id"]
    max_seats = event_data["max_seats_per_table"]

    updated_data = {"event_id": event_id, "table_number": 2, "seats": max_seats}

    response = test_client.put("/api/tables/9999", json=updated_data)

    assert response.status_code == 404, f"Unexpected error: {response.json()}"


# Tests for DELETE /api/tables/{table_id}
def test_delete_table_success(test_client: TestClient) -> None:
    """Test successful deletion of a table."""
    # Arrange
    event_data = create_event_with_isoformat(test_client)
    event_id = event_data["id"]
    max_seats = event_data["max_seats_per_table"]

    table_id = create_table(test_client, event_id, seats=max_seats)

    # Act
    response = test_client.delete(f"/api/tables/{table_id}")

    # Assert
    assert response.status_code == 204
    response = test_client.get(f"/api/tables/{table_id}")
    assert response.status_code == 404


def test_delete_table_not_found(test_client: TestClient) -> None:
    """Test deletion of a non-existent table returns 404."""
    # Act
    response = test_client.delete("/api/tables/9999")

    # Assert
    assert response.status_code == 404


# Additional test
def test_table_repr() -> None:
    """Validate the string representation of a Table instance."""
    table = Table(id=1, event_id=2, table_number=1, seats=8)

    expected_output = (
        f"<Table id={table.id} event_id={table.event_id} table_number={table.table_number} seats={table.seats}>"
    )
    assert repr(table) == expected_output
