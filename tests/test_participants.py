# tests/test_participants.py
import pytest
from fastapi.testclient import TestClient
from pytest_mock import MockerFixture
from sqlalchemy.orm import Session

from src.models.participant import Participant
from tests.helpers import create_event_with_isoformat, create_participant, generate_unique_participant


# CRUD Tests for /api/participants/
def test_participant_creation_success(client: TestClient) -> None:
    """Test successful creation of a participant."""
    # Arrange
    event_data = create_event_with_isoformat(client)
    event_id = event_data["id"]
    participant_data = generate_unique_participant(event_id)

    # Act
    response = client.post("/api/participants/", json=participant_data.model_dump())

    # Assert
    assert response.status_code == 201
    response_data = response.json()
    assert response_data["full_name"] == participant_data.full_name
    assert response_data["company_name"] == participant_data.company_name
    assert response_data["is_present"] is False


def test_get_participant(client: TestClient) -> None:
    """Test retrieving a participant by ID."""
    # Arrange
    event_data = create_event_with_isoformat(client)
    event_id = event_data["id"]
    participant_id = create_participant(client, event_id)

    # Act
    response = client.get(f"/api/participants/{participant_id}")

    # Assert
    assert response.status_code == 200
    assert response.json()["id"] == participant_id


def test_get_participant_list(client: TestClient) -> None:
    """Test retrieving the list of all participants."""
    # Arrange
    event_data = create_event_with_isoformat(client)
    event_id = event_data["id"]
    create_participant(client, event_id)

    # Act
    response = client.get("/api/participants/")

    # Assert
    assert response.status_code == 200
    assert len(response.json()) > 0


def test_update_participant(client: TestClient) -> None:
    """Test updating a participant's details."""
    # Arrange
    event_data = create_event_with_isoformat(client)
    event_id = event_data["id"]
    participant_id = create_participant(client, event_id)
    updated_data = {
        "full_name": "Updated Name",
        "company_name": "Updated Company",
        "whatsapp": "+5511998888888",
        "email": "updated@example.com",
        "event_id": event_id,
        "custom_data": {"updated_key": "updated_value"},
    }

    # Act
    response = client.put(f"/api/participants/{participant_id}", json=updated_data)

    # Assert
    assert response.status_code == 200
    assert response.json()["full_name"] == updated_data["full_name"]


def test_delete_participant_success(client: TestClient, db_session: Session) -> None:
    """Test successful deletion of a participant by ID."""
    # Arrange
    event_data = create_event_with_isoformat(client)
    event_id = event_data["id"]
    participant_id = create_participant(client, event_id)

    # Act
    response = client.delete(f"/api/participants/{participant_id}")

    # Assert
    assert response.status_code == 204

    response = client.get(f"/api/participants/{participant_id}")
    assert response.status_code == 404


def test_check_in_participant_success(client: TestClient) -> None:
    """Test successful check-in of a participant."""
    # Arrange
    event_data = create_event_with_isoformat(client)
    event_id = event_data["id"]
    participant_id = create_participant(client, event_id)

    # Act
    response = client.post(f"/api/participants/{participant_id}/check-in")

    # Assert
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["is_present"] is True
    assert response_data["id"] == participant_id


def test_check_in_participant_not_found(client: TestClient) -> None:
    """Test check-in for a non-existent participant returns 404."""
    # Act
    response = client.post("/api/participants/9999/check-in")

    # Assert
    assert response.status_code == 404
    response_data = response.json()
    assert response_data["detail"] == "Participant not found"


@pytest.mark.skip(reason="Complex setup; revisit in future.")
def test_check_in_participant_unexpected_error(mocker: MockerFixture, client: TestClient) -> None:
    """Test unexpected error during participant check-in."""
    # Arrange
    event_data = create_event_with_isoformat(client)
    event_id = event_data["id"]
    participant_id = create_participant(client, event_id)

    # Mock `db.commit` to raise an exception
    mocker.patch(
        "src.services.participant_service.check_in_participant", side_effect=Exception("Mocked unexpected error")
    )

    # Act
    response = client.post(f"/api/participants/{participant_id}/check-in")

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
