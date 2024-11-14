# tests/test_allocation.py
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.helpers import add_participant, check_in_participant, create_event_with_isoformat, create_table


def test_preview_allocation(client: TestClient, db_session: Session) -> None:
    """Test preview allocation for completed allocations."""
    # Arrange
    event_data = create_event_with_isoformat(client)
    event_id = event_data["id"]
    create_table(client, event_id=event_id)

    # Add participants and confirm allocation to generate data
    for _ in range(10):
        participant = add_participant(db_session, event_id=event_id)
        check_in_participant(db_session, participant.id)

    # Confirm allocation before preview
    client.post(f"/api/events/{event_id}/allocation/confirm")

    # Act
    response = client.get(f"/api/events/{event_id}/allocation/preview")

    # Assert
    assert response.status_code == 200, "Expected 200 OK for preview allocation."
    allocations = response.json()
    assert isinstance(allocations, list), "Expected a list of allocations for the preview."
    assert len(allocations) > 0, "Expected at least one allocation round."


def test_confirm_allocation_checked_in_only(client: TestClient, db_session: Session) -> None:
    """
    Test allocation confirmation endpoint for checked-in participants,
    ensuring that only checked-in participants are allocated.
    """
    # Arrange
    num_participants = 10
    seats_per_table = 4
    event_data = create_event_with_isoformat(client)
    event_id = event_data["id"]
    create_table(client, event_id=event_id, seats=seats_per_table)

    # Add participants and check in half of them
    checked_in_participants = []
    for _ in range(num_participants):
        participant = add_participant(db_session, event_id=event_id)
        if _ < num_participants // 2:  # Only check-in half
            check_in_participant(db_session, participant.id)
            checked_in_participants.append(participant.id)

    # Act
    response = client.post(f"/api/events/{event_id}/allocation/confirm")

    # Assert
    assert response.status_code == 201, "Expected 201 Created for allocation confirmation."
    rounds_summary = response.json()

    # Verify only checked-in participants are in the allocation
    allocated_participants = set()
    for allocation in rounds_summary:
        for table in allocation["allocations"]:
            allocated_participants.update(table["participant_ids"])

    assert set(allocated_participants) == set(
        checked_in_participants
    ), "Only checked-in participants should be allocated."
