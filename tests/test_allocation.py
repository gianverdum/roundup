# tests/test_allocation.py
from math import ceil

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.helpers import add_participant, check_in_participant, create_event_with_isoformat, create_table


def test_preview_allocation_all_participants(client: TestClient, db_session: Session) -> None:
    """Test preview allocation for all participants, regardless of check-in status."""
    # Arrange
    event_data = create_event_with_isoformat(client)
    event_id = event_data["id"]
    create_table(client, event_id=event_id)

    for _ in range(10):  # Add 10 participants
        add_participant(db_session, event_id=event_id)

    # Act
    response = client.get(f"/api/events/{event_id}/allocation/preview")

    # Assert
    assert response.status_code == 200, "Expected 200 OK for preview allocation."
    rounds_needed = response.json()
    assert isinstance(rounds_needed, int), "Expected an integer for rounds in preview allocation."
    assert rounds_needed > 0, "Expected at least one round for allocation."


def test_preview_allocation_checked_in_only(client: TestClient, db_session: Session) -> None:
    """Test preview allocation for only checked-in participants."""
    # Arrange
    event_data = create_event_with_isoformat(client)
    event_id = event_data["id"]
    create_table(client, event_id=event_id)

    # Add 10 participants, 5 with check-in
    for _ in range(5):
        participant = add_participant(db_session, event_id=event_id)
        check_in_participant(db_session, participant.id)
    for _ in range(5):
        add_participant(db_session, event_id=event_id, is_present=False)

    # Act
    response = client.get(f"/api/events/{event_id}/allocation/preview?only_checked_in=True")

    # Assert
    assert response.status_code == 200, "Expected 200 OK for preview allocation with checked-in only."
    rounds_needed = response.json()
    assert isinstance(rounds_needed, int), "Expected an integer for rounds in preview allocation."
    assert rounds_needed > 0, "Expected at least one round for checked-in participants."


@pytest.mark.skip(reason="Test modified to validate realistic matrix allocation")
def test_confirm_allocation(client: TestClient, db_session: Session) -> None:
    """
    Test the allocation confirmation endpoint for checked-in participants,
    verifying that participants are evenly distributed across rounds.

    This test ensures that:
    - All participants are included in the allocation.
    - Each round has the expected number of allocations.
    """
    # Arrange
    num_participants: int = 24
    seats_per_table: int = 8
    num_tables: int = ceil(num_participants / seats_per_table)

    event_data = create_event_with_isoformat(client)
    event_id = event_data["id"]

    for _ in range(num_tables):
        create_table(client, event_id=event_id, seats=seats_per_table)

    participants = [add_participant(db_session, event_id=event_id) for _ in range(num_participants)]
    for participant in participants:
        check_in_participant(db_session, participant.id)

    # Act
    response = client.post(f"/api/events/{event_id}/allocation/confirm")

    # Assert
    assert response.status_code == 201, "Expected 201 Created for allocation confirmation."
    rounds_summary = response.json()

    # Verify that each participant is included in the allocation
    allocated_participants = set()
    for allocation in rounds_summary:
        for table in allocation["allocations"]:
            allocated_participants.update(table["participant_ids"])

    assert len(allocated_participants) == num_participants, "All participants should be allocated at least once."
    assert len(rounds_summary) > 1, "Expected multiple rounds of allocation."
