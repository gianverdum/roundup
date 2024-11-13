# tests/test_allocation.py
from typing import List, Set, Tuple

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.models.round import Round
from src.models.table_allocation import TableAllocation
from tests.helpers import add_participant, check_in_participant, create_event_with_isoformat, create_table


def test_preview_allocation_all_participants(client: TestClient, db_session: Session) -> None:
    """Test preview allocation for all participants, regardless of check-in status."""
    # Arrange: Set up event, tables, and participants
    event_data = create_event_with_isoformat(client)
    event_id = event_data["id"]
    create_table(client, event_id=event_id)

    for _ in range(10):  # Add 10 participants
        add_participant(db_session, event_id=event_id)

    # Act: Call the preview allocation endpoint
    response = client.get(f"/api/events/{event_id}/allocation/preview")

    # Assert: Check the estimated number of rounds
    assert response.status_code == 200
    rounds_needed = response.json()
    assert rounds_needed > 0, "Expected at least one round for allocation."
    # Additional check for return type consistency
    assert isinstance(rounds_needed, int), "Expected preview allocation to return an integer value for rounds."


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
    assert response.status_code == 200
    rounds_needed = response.json()
    assert rounds_needed > 0, "Expected at least one round for checked-in participants."
    assert isinstance(rounds_needed, int), "Expected preview allocation to return an integer."


def test_confirm_allocation(client: TestClient, db_session: Session) -> None:
    """Test confirm allocation for checked-in participants and verify database consistency."""
    # Arrange
    event_data = create_event_with_isoformat(client)
    event_id = event_data["id"]
    create_table(client, event_id=event_id)

    participants = [add_participant(db_session, event_id=event_id, full_name=f"Participant {i+1}") for i in range(10)]
    for p in participants:
        check_in_participant(db_session, p.id)

    # Act
    response = client.post(f"/api/events/{event_id}/allocation/confirm")

    # Assert
    assert response.status_code == 201
    rounds_summary = response.json()
    assert len(rounds_summary) > 0, "Expected at least one round in allocation confirmation."

    # Additional checks to ensure allocations are persisted correctly
    rounds_in_db: List[Round] = db_session.query(Round).filter(Round.event_id == event_id).all()
    assert len(rounds_in_db) == len(rounds_summary), "Mismatch between rounds in DB and summary returned."

    # Ensure that we have a list of integer IDs for the query
    round_ids: List[int] = [r.id for r in rounds_in_db if isinstance(r.id, int)]

    allocations_in_db = (
        db_session.query(TableAllocation).filter(TableAllocation.round_id.in_(round_ids)).all()  # type: ignore
    )
    allocated_participants = {ta.participant_id for ta in allocations_in_db}
    assert len(allocated_participants) == len(participants), "All participants should be allocated."

    # Verify unique grouping of participants across all rounds, ensuring expected interactions
    unique_interactions: Set[Tuple[int, int]] = set()
    for allocation in rounds_summary:
        for table in allocation["allocations"]:
            participants_at_table = table["participant_ids"]
            for i, p1 in enumerate(participants_at_table):
                for p2 in participants_at_table[i + 1 :]:
                    unique_interactions.add(tuple(sorted((p1, p2))))

    # Total possible unique pairs (combinations) for the participants
    total_possible_pairs = len(participants) * (len(participants) - 1) // 2
    assert len(unique_interactions) == total_possible_pairs, "Not all unique interactions were created."
