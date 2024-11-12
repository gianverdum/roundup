# src/routers/allocation.py
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.database import get_db
from src.models.event import Event
from src.models.participant import Participant
from src.models.round import Round
from src.models.table import Table
from src.models.table_allocation import TableAllocation
from src.schemas.round_summary import RoundSummary, TableAllocationSummary
from src.services.allocation_service import allocate_participants, calculate_rounds_needed

router = APIRouter()


@router.get(
    "/events/{event_id}/allocation/preview",
    response_model=int,
    summary="Preview Allocation Rounds",
    responses={
        200: {
            "description": "Estimated number of rounds for unique participant interactions",
            "content": {"application/json": {"example": 3}},
        },
        400: {"description": "No participants available for allocation"},
        404: {"description": "Event not found"},
    },
)
def preview_allocation(event_id: int, only_checked_in: bool = False, db: Session = Depends(get_db)) -> int:
    """
    Provides a preview of the number of rounds required for unique participant interactions.

    Parameters:
        - event_id (int): ID of the event to preview allocation for.
        - only_checked_in (bool): If True, only participants who checked in are considered.
        - db (Session): Database session dependency.

    Returns:
        int: The estimated number of rounds needed.
    """
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found.")

    # Filter participants based on check-in status if only_checked_in is True
    participants_query = db.query(Participant).filter(Participant.event_id == event_id)
    if only_checked_in:
        participants_query = participants_query.filter(Participant.is_present.is_(True))

    participants = participants_query.all()
    if not participants:
        raise HTTPException(status_code=400, detail="No participants available for allocation.")

    rounds_needed = calculate_rounds_needed(len(participants), event.max_seats_per_table, event.tables_count)
    return rounds_needed


@router.post(
    "/events/{event_id}/allocation/confirm",
    response_model=List[RoundSummary],
    status_code=status.HTTP_201_CREATED,
    summary="Confirm Allocation",
    responses={
        201: {
            "description": "Confirmed participant allocation across tables and rounds",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "round_number": 1,
                            "allocations": [
                                {"table_id": 1, "participant_ids": [1, 2, 3]},
                                {"table_id": 2, "participant_ids": [4, 5, 6]},
                            ],
                        },
                        {
                            "round_number": 2,
                            "allocations": [
                                {"table_id": 1, "participant_ids": [7, 8, 9]},
                                {"table_id": 2, "participant_ids": [10, 11, 12]},
                            ],
                        },
                    ]
                }
            },
        },
        400: {"description": "No participants available for allocation"},
        404: {"description": "Event not found"},
    },
)
def confirm_allocation(event_id: int, db: Session = Depends(get_db)) -> List[RoundSummary]:
    """
    Confirms and saves participant allocation across tables and rounds.

    Parameters:
        - event_id (int): ID of the event to confirm allocation for.
        - db (Session): Database session dependency.

    Returns:
        List[RoundSummary]: List of round summaries showing table allocations per round.
    """
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found.")

    # Retrieve participants who have checked in
    participants = (
        db.query(Participant).filter(Participant.event_id == event_id, Participant.is_present.is_(True)).all()
    )
    if not participants:
        raise HTTPException(status_code=400, detail="No participants available for allocation.")

    tables = db.query(Table).filter(Table.event_id == event_id).all()
    rounds_needed = calculate_rounds_needed(len(participants), event.max_seats_per_table, event.tables_count)

    # Perform allocation
    allocations = allocate_participants([p.id for p in participants], tables, max_rounds=rounds_needed)

    round_summaries = []
    for round_number, allocation in allocations.items():
        # Create and persist each round in the database
        round_entry = Round(event_id=event_id, round_number=round_number)
        db.add(round_entry)
        db.flush()  # Flush to assign an ID to round_entry for relationships

        table_allocations = []
        for table_id, participant_ids in allocation.items():
            for participant_id in participant_ids:
                table_allocation = TableAllocation(
                    round_id=round_entry.id, table_id=table_id, participant_id=participant_id
                )
                db.add(table_allocation)
                table_allocations.append(table_allocation)

        # Build RoundSummary for the response
        round_summary = RoundSummary(
            round_number=round_number,
            allocations=[
                TableAllocationSummary(table_id=table_id, participant_ids=participant_ids)
                for table_id, participant_ids in allocation.items()
            ],
        )
        round_summaries.append(round_summary)

    db.commit()  # Commit all changes to the database
    return round_summaries
