# tests/test_tables.py

from fastapi.testclient import TestClient

from src.models.table import Table
from tests.helpers import create_event_with_isoformat, create_table, generate_data_table


# Tests for POST /api/tables/
def test_table_creation_success(client: TestClient) -> None:
    """Test successful creation of tables."""
    # Arrange
    event_data = create_event_with_isoformat(client)
    event_id = event_data["id"]
    max_seats = event_data["max_seats_per_table"]

    table_data = generate_data_table(event_id, quantity=3, seats=max_seats)

    # Act
    response = client.post("/api/tables/", json=table_data.model_dump())

    # Assert
    assert response.status_code == 201
    response_data = response.json()
    assert len(response_data) == 3
    assert all(table["seats"] == max_seats for table in response_data)


def test_table_creation_with_missing_fields(client: TestClient) -> None:
    """Test that missing fields result in a 422 error."""
    # Arrange
    event_data = create_event_with_isoformat(client)
    event_id = event_data["id"]

    # Act
    response = client.post("/api/tables/", json={"event_id": event_id})

    # Assert
    assert response.status_code == 422


# Tests for GET /api/tables/
def test_get_all_tables_success(client: TestClient) -> None:
    """Test retrieval of all tables."""
    # Arrange
    event_data = create_event_with_isoformat(client)
    event_id = event_data["id"]
    max_seats = event_data["max_seats_per_table"]

    create_table(client, event_id, seats=max_seats)

    # Act
    response = client.get("/api/tables/")

    # Assert
    assert response.status_code == 200
    assert isinstance(response.json()["items"], list)


# Tests for GET /api/tables/filter
def test_filter_tables(client: TestClient) -> None:
    """Test filtering tables by specific criteria."""
    # Arrange
    event_data = create_event_with_isoformat(client)
    event_id = event_data["id"]
    max_seats = event_data["max_seats_per_table"]

    create_table(client, event_id, seats=max_seats)

    # Act
    response = client.get(f"/api/tables/filter?event_id={event_id}")

    # Assert
    assert response.status_code == 200
    response_data = response.json()
    assert isinstance(response_data["items"], list)
    assert len(response_data["items"]) >= 1


# Tests for GET /api/tables/{table_id}
def test_get_table_by_id_success(client: TestClient) -> None:
    """Test retrieval of a table by its ID."""
    # Arrange
    event_data = create_event_with_isoformat(client)
    event_id = event_data["id"]
    max_seats = event_data["max_seats_per_table"]

    table_id = create_table(client, event_id, seats=max_seats)

    # Act
    response = client.get(f"/api/tables/{table_id}")

    # Assert
    assert response.status_code == 200
    assert response.json()["id"] == table_id


def test_get_table_by_id_not_found(client: TestClient) -> None:
    """Test retrieval of a non-existent table returns 404."""
    # Arrange/Act
    response = client.get("/api/tables/9999")

    # Assert
    assert response.status_code == 404


# Tests for PUT /api/tables/{table_id}
def test_update_table_success(client: TestClient) -> None:
    """Test successful update of a table."""
    # Arrange
    event_data = create_event_with_isoformat(client)
    event_id = event_data["id"]
    max_seats = event_data["max_seats_per_table"]

    table_id = create_table(client, event_id, seats=max_seats)
    updated_data = {"event_id": event_id, "table_number": 2, "seats": max_seats}

    # Act
    response = client.put(f"/api/tables/{table_id}", json=updated_data)

    # Assert
    assert response.status_code == 200, f"Unexpected error: {response.json()}"
    response_data = response.json()
    assert response_data["table_number"] == updated_data["table_number"]


def test_update_table_not_found(client: TestClient) -> None:
    """Test updating a non-existent table returns 404."""
    # Arrange
    event_data = create_event_with_isoformat(client)
    event_id = event_data["id"]
    max_seats = event_data["max_seats_per_table"]

    updated_data = {"event_id": event_id, "table_number": 2, "seats": max_seats}

    # Act
    response = client.put("/api/tables/9999", json=updated_data)

    # Assert
    assert response.status_code == 404, f"Unexpected error: {response.json()}"


# Tests for DELETE /api/tables/{table_id}
def test_delete_table_success(client: TestClient) -> None:
    """Test successful deletion of a table."""
    # Arrange
    event_data = create_event_with_isoformat(client)
    event_id = event_data["id"]
    max_seats = event_data["max_seats_per_table"]

    table_id = create_table(client, event_id, seats=max_seats)

    # Act
    response = client.delete(f"/api/tables/{table_id}")

    # Assert
    assert response.status_code == 204
    response = client.get(f"/api/tables/{table_id}")
    assert response.status_code == 404


def test_delete_table_not_found(client: TestClient) -> None:
    """Test deletion of a non-existent table returns 404."""
    # Arrange/Act
    response = client.delete("/api/tables/9999")

    # Assert
    assert response.status_code == 404


# Additional test
def test_table_repr() -> None:
    """Validate the string representation of a Table instance."""
    # Arrange/Act
    table = Table(id=1, event_id=2, table_number=1, seats=8)

    expected_output = (
        f"<Table id={table.id} event_id={table.event_id} table_number={table.table_number} seats={table.seats}>"
    )

    # Assert
    assert repr(table) == expected_output
