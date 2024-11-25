# src/services/allocation_service.py
import random
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from src.models.participant import Participant
from src.models.round import Round
from src.models.table import Table
from src.models.table_allocation import TableAllocation
from src.schemas.round_summary import RoundSummary, TableAllocationSummary


def allocate_participants(
    participants: List[int], tables: List[Table], max_rounds: Optional[int] = None
) -> Dict[int, Dict[int, List[int]]]:
    """
    Allocate participants across rounds to maximize unique encounters within specified rounds.

    Parameters:
        - participants (List[int]): List of participant IDs.
        - tables (List[Table]): List of table configurations.
        - max_rounds (Optional[int]): Maximum number of rounds for allocation.

    Returns:
        Dict[int, Dict[int, List[int]]]: A dictionary with rounds as keys and table allocations.
    """

    encounters: Dict[int, set[int]] = {p: set() for p in participants}
    rounds = {}
    table_capacity = tables[0].seats  # Assumes all tables have the same capacity
    num_tables = len(tables)  # Define o número de mesas com base no tamanho da lista tables

    # If max_rounds is not provided, set it to the number of tables
    if max_rounds is None:
        max_rounds = num_tables

    for round_number in range(1, max_rounds + 1):
        random.shuffle(participants)  # Shuffle participants to create random groups
        allocation = {}

        # Allocate participants to tables in groups
        for i in range(num_tables):
            table_participants = participants[i * table_capacity : (i + 1) * table_capacity]
            allocation[tables[i].id] = table_participants

            # Update encounters for each participant
            for p1 in table_participants:
                for p2 in table_participants:
                    if p1 != p2:
                        encounters[p1].add(p2)

        # Add the allocation to the rounds
        rounds[round_number] = allocation

        # Check if maximum unique encounters are reached
        all_encounters_met = all(len(encounters[p]) >= len(participants) - 1 for p in participants)
        if all_encounters_met:
            break

    return rounds


def get_completed_allocations(event_id: int, db: Session) -> List[RoundSummary]:
    """
    Retrieve completed allocations for a specific event.

    Parameters:
        - event_id (int): ID of the event.
        - db (Session): Database session dependency.

    Returns:
        List[RoundSummary]: List of round summaries showing table allocations per round.
    """
    rounds = db.query(Round).filter(Round.event_id == event_id).order_by(Round.round_number).all()

    if not rounds:
        return []

    round_summaries = []
    for round_entry in rounds:
        table_allocations = db.query(TableAllocation).filter(TableAllocation.round_id == round_entry.id).all()
        allocation_summary = [
            TableAllocationSummary(table_id=allocation.table_id, participant_ids=[allocation.participant_id])
            for allocation in table_allocations
        ]
        round_summary = RoundSummary(
            round_number=round_entry.round_number,
            allocations=allocation_summary,
        )
        round_summaries.append(round_summary)

    return round_summaries


def get_allocation_by_participant(event_id: int, participant_id: int, db: Session) -> Dict[str, Dict[str, int]]:
    """
    Retrieve allocation details for a specific participant across rounds in an event.

    Parameters:
        - event_id (int): ID of the event.
        - participant_id (int): ID of the participant.
        - db (Session): Database session dependency.

    Returns:
        Dict[str, Dict[str, int]]: Dictionary mapping rounds to allocated tables.
    """
    allocations = (
        db.query(TableAllocation)
        .join(Round, TableAllocation.round_id == Round.id)
        .join(Table, TableAllocation.table_id == Table.id)
        .filter(Round.event_id == event_id, TableAllocation.participant_id == participant_id)
        .order_by(Round.round_number)
        .all()
    )

    if not allocations:
        return {}

    return {
        f"Round {allocation.round.round_number}": {"table_number": allocation.table.table_number}
        for allocation in allocations
    }


def get_allocation_by_event(event_id: int, db: Session) -> Dict[str, Dict[str, List[str]]]:
    """
    Retrieve allocation details for all participants grouped by rounds and tables in an event.

    Parameters:
        - event_id (int): ID of the event.
        - db (Session): Database session dependency.

    Returns:
        Dict[str, Dict[str, List[str]]]: Dictionary with allocation grouped by rounds and tables.
    """
    allocations = (
        db.query(TableAllocation)
        .join(Round, TableAllocation.round_id == Round.id)
        .join(Table, TableAllocation.table_id == Table.id)
        .join(Participant, TableAllocation.participant_id == Participant.id)
        .filter(Round.event_id == event_id)
        .order_by(Round.round_number, Table.table_number)
        .all()
    )

    if not allocations:
        return {}

    grouped_allocations: Dict[str, Dict[str, List[str]]] = {}

    for allocation in allocations:
        round_key = f"Round {allocation.round.round_number}"
        table_key = f"Table {allocation.table.table_number}"

        if round_key not in grouped_allocations:
            grouped_allocations[round_key] = {}

        if table_key not in grouped_allocations[round_key]:
            grouped_allocations[round_key][table_key] = []

        grouped_allocations[round_key][table_key].append(allocation.participant.full_name)

    return grouped_allocations
