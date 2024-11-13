# tests/test_events.py
from datetime import datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.models.event import Event
from tests.helpers import create_event_with_isoformat, generate_unique_event


# Tests for POST /api/events/
def test_event_creation_success(client: TestClient, db_session: Session) -> None:
    """Test successful creation of an event."""
    # Arrange
    event_data = generate_unique_event()
    event_data_dict = event_data.model_dump()
    event_data_dict["date"] = event_data.date.isoformat()

    # Act
    response = client.post("/api/events/", json=event_data_dict)

    # Assert
    assert response.status_code == 201
    response_data = response.json()
    assert response_data["name"] == event_data.name


def test_event_creation_with_past_date(client: TestClient, db_session: Session) -> None:
    """Test that an event cannot be created with a past date."""
    # Arrange
    event_data = generate_unique_event()
    past_date = datetime.now() - timedelta(days=1)
    event_data.date = past_date
    event_data_dict = event_data.model_dump()
    event_data_dict["date"] = past_date.isoformat()

    # Act
    response = client.post("/api/events/", json=event_data_dict)

    # Assert
    assert response.status_code == 422
    response_data = response.json()
    assert response_data["detail"][0]["msg"] == "Value error, The event date cannot be in the past."


# Tests for GET /api/events/
def test_get_all_events_success(client: TestClient, db_session: Session) -> None:
    """Test retrieval of all events."""
    # Arrange
    create_event_with_isoformat(client)

    # Act
    response = client.get("/api/events/")

    # Assert
    assert response.status_code == 200
    response_data = response.json()
    assert isinstance(response_data["items"], list)
    assert response_data["total_items"] >= 1


# Tests for GET /api/events/filter
def test_filter_events(client: TestClient, db_session: Session) -> None:
    """Test event filtering based on criteria."""
    # Arrange
    create_event_with_isoformat(client)

    # Act
    response = client.get("/api/events/filter?name=Event")

    # Assert
    assert response.status_code == 200
    response_data = response.json()
    assert isinstance(response_data["items"], list)
    assert len(response_data["items"]) >= 1


# Tests for GET /api/events/{event_id}
def test_get_event_by_id_success(client: TestClient, db_session: Session) -> None:
    """Test retrieval of an event by ID."""
    # Arrange
    event_data = create_event_with_isoformat(client)
    event_id = event_data["id"]  # Extrai apenas o ID

    # Act
    response = client.get(f"/api/events/{event_id}")

    # Assert
    assert response.status_code == 200
    assert response.json()["id"] == event_id


def test_get_event_by_id_not_found(client: TestClient, db_session: Session) -> None:
    """Test retrieval of a non-existent event returns 404."""
    # Arrange/Act
    response = client.get("/api/events/9999")

    # Assert
    assert response.status_code == 404


# Tests for PUT /api/events/{event_id}
def test_update_event_success(client: TestClient, db_session: Session) -> None:
    """Test successful update of an event."""
    # Arrange
    event_data = create_event_with_isoformat(client)
    event_id = event_data["id"]  # Extrai apenas o ID
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
    response = client.put(f"/api/events/{event_id}", json=updated_data)

    # Assert
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["name"] == updated_data["name"]


def test_update_event_not_found(client: TestClient, db_session: Session) -> None:
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
    response = client.put("/api/events/9999", json=updated_data)

    # Assert
    assert response.status_code == 404


# Tests for DELETE /api/events/{event_id}
def test_delete_event_success(client: TestClient, db_session: Session) -> None:
    """Test successful deletion of an event by ID."""
    # Arrange
    event_data = create_event_with_isoformat(client)
    event_id = event_data["id"]  # Extrai apenas o ID

    # Act
    response = client.delete(f"/api/events/{event_id}")

    # Assert
    assert response.status_code == 204
    response = client.get(f"/api/events/{event_id}")
    assert response.status_code == 404


def test_delete_event_not_found(client: TestClient, db_session: Session) -> None:
    """Test deletion of a non-existent event returns 404."""
    # Arrange/Act
    response = client.delete("/api/events/9999")

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
