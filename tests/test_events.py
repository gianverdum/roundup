# tests/test_events.py
from datetime import datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


def test_event_creation_success(test_client: TestClient, db_session: Session) -> None:
    """
    Validate successful creation of a new event via POST request.

    This test checks:
    - The response status code is 201.
    - The response data matches the input data.
    - The response includes a valid event ID in integer format.
    """

    # Arrange
    event_data = {
        "name": "Annual Business Round",
        "date": (datetime.now() + timedelta(days=1)).isoformat(),
        "location": "Business Center, São Paulo",
        "address": "Av. Paulista, 1000 - Bela Vista, São Paulo - SP, 01310-000",
        "participant_limit": 50,
    }

    # Act
    response = test_client.post("/events/", json=event_data)

    # Debugging output
    print("Response Body:", response.json())
    print("Response Content:", response.content)

    # Assert
    assert response.status_code == 201, f"Expected 201, got {response.status_code}"

    # Validate response structure and content
    response_data = response.json()
    assert "id" in response_data, "Response missing 'id' field"
    assert isinstance(response_data["id"], int), "ID should be an integer"
    assert response_data["id"] > 0, "ID should be a positive integer"

    # Check if other fields match the input data
    assert response_data["name"] == event_data["name"], "Event name mismatch"
    assert response_data["location"] == event_data["location"], "Location mismatch"
    assert response_data["address"] == event_data["address"], "Address mismatch"
    assert response_data["participant_limit"] == event_data["participant_limit"], "Participant limit mismatch"
