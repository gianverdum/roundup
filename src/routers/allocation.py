# src/routers/allocation.py
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.database import get_db
from src.models.event import Event
from src.models.participant import Participant
from src.models.round import Round
from src.models.table import Table
from src.models.table_allocation import TableAllocation
from src.schemas.round_summary import RoundSummary, TableAllocationSummary
from src.services.allocation_service import (
    allocate_participants,
    get_allocation_by_event,
    get_allocation_by_participant,
    get_completed_allocations,
)

router = APIRouter()


@router.get(
    "/api/events/{event_id}/allocation/preview",
    response_model=List[RoundSummary],
    status_code=status.HTTP_200_OK,
    summary="Retrieve Completed Allocations",
    responses={
        200: {
            "description": "Retrieve participant allocations across rounds",
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
                    ]
                }
            },
        },
        404: {"description": "Event not found or no allocations exist"},
    },
)
def get_completed_allocations_route(event_id: int, db: Session = Depends(get_db)) -> List[RoundSummary]:
    """
    Retrieve completed allocations for the event.

    Parameters:
        - event_id (int): ID of the event to retrieve allocations for.
        - db (Session): Database session dependency.

    Returns:
        List[RoundSummary]: List of round summaries showing table allocations per round.
    """
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found.")

    round_summaries = get_completed_allocations(event_id=event_id, db=db)

    if not round_summaries:
        raise HTTPException(status_code=404, detail="No allocations exist for this event.")

    return round_summaries


@router.get(
    "/api/events/{event_id}/allocation/by-participant",
    response_model=Dict[str, Dict[str, int]],
    status_code=status.HTTP_200_OK,
    summary="Retrieve allocation details by participant",
    responses={
        200: {
            "description": "Allocation details for a participant returned successfully.",
            "content": {
                "application/json": {
                    "example": {
                        "Round 1": {"table_number": 5},
                        "Round 2": {"table_number": 3},
                        "Round 3": {"table_number": 7},
                    }
                }
            },
        },
        404: {
            "description": "Participant not found or no allocations exist for the event.",
            "content": {
                "application/json": {
                    "example": {"detail": "No allocation found for the specified participant and event."}
                }
            },
        },
    },
)
def get_allocation_by_participant_route(
    event_id: int, participant_id: int, db: Session = Depends(get_db)
) -> Dict[str, Dict[str, int]]:
    """
    Retrieve allocation details for a specific participant in an event.

    Parameters:
        - event_id (int): ID of the event.
        - participant_id (int): ID of the participant.
        - db (Session): Database session dependency.

    Returns:
        Dict[str, Dict[str, int]]: Allocation details for the participant across rounds.
    """
    allocation = get_allocation_by_participant(event_id=event_id, participant_id=participant_id, db=db)

    if not allocation:
        raise HTTPException(status_code=404, detail="No allocation found for the specified participant and event.")

    return allocation


@router.get(
    "/api/events/{event_id}/allocation/by-event",
    response_model=Dict[str, Dict[str, List[str]]],
    status_code=status.HTTP_200_OK,
    summary="Retrieve allocation details for all participants in the event",
    responses={
        200: {
            "description": "Allocation details for the event returned successfully.",
            "content": {
                "application/json": {
                    "example": {
                        "Round 1": {
                            "Table 1": ["Participant A", "Participant B"],
                            "Table 2": ["Participant C", "Participant D"],
                        },
                        "Round 2": {
                            "Table 1": ["Participant E", "Participant F"],
                            "Table 2": ["Participant G", "Participant H"],
                        },
                    }
                }
            },
        },
        404: {
            "description": "No allocations exist for the event.",
            "content": {
                "application/json": {"example": {"detail": "No allocation data found for the specified event."}}
            },
        },
    },
)
def get_allocation_by_event_route(event_id: int, db: Session = Depends(get_db)) -> Dict[str, Dict[str, List[str]]]:
    """
    Retrieve allocation details for all participants in an event grouped by rounds and tables.

    Parameters:
        - event_id (int): ID of the event.
        - db (Session): Database session dependency.

    Returns:
        Dict[str, Dict[str, List[str]]]: Allocation details grouped by round and table.
    """
    allocation = get_allocation_by_event(event_id=event_id, db=db)

    if not allocation:
        raise HTTPException(status_code=404, detail="No allocation data found for the specified event.")

    return allocation


@router.post(
    "/api/events/{event_id}/allocation/confirm",
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
                    ]
                }
            },
        },
        400: {"description": "No participants available for allocation"},
        404: {"description": "Event not found"},
    },
)
def confirm_allocation(
    event_id: int, max_rounds: Optional[int] = None, db: Session = Depends(get_db)
) -> List[RoundSummary]:
    """
    Confirms and saves participant allocation across tables and rounds.

    Parameters:
        - event_id (int): ID of the event to confirm allocation for.
        - max_rounds (Optional[int]): Maximum number of rounds for allocation.
        - db (Session): Database session dependency.

    Returns:
        List[RoundSummary]: List of round summaries showing table allocations per round.
    """
    # Check if event exists
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found.")

    # Retrieve checked-in participants
    participants = (
        db.query(Participant).filter(Participant.event_id == event_id, Participant.is_present.is_(True)).all()
    )
    if not participants:
        raise HTTPException(status_code=400, detail="No participants available for allocation.")

    # Retrieve event tables
    tables = db.query(Table).filter(Table.event_id == event_id).all()

    # Perform allocation with max_rounds
    allocations = allocate_participants(participants=[p.id for p in participants], tables=tables, max_rounds=max_rounds)

    # Save rounds and allocations to the database
    round_summaries = []
    for round_number, allocation in allocations.items():
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

        # Create summary for response
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
