# tests/test_allocation_service.py
from typing import List, Set, Tuple

import pytest

from src.models.table import Table
from src.services.allocation_service import allocate_participants


@pytest.mark.parametrize(
    "table_quantity, seats_per_table, participants",
    [(5, 4, 20), (12, 8, 96)],  # Moderate test case  # Larger test case for robustness
)
def test_no_repeated_table_groups_across_rounds(table_quantity: int, seats_per_table: int, participants: int) -> None:
    """
    Test allocation to ensure no repeated groups across rounds, allowing groups smaller than full capacity,
    but disallowing single-participant groups.
    """
    # Arrange
    tables: List[Table] = [Table(id=i, seats=seats_per_table) for i in range(1, table_quantity + 1)]
    participant_ids: List[int] = list(range(1, participants + 1))

    # Act
    rounds = allocate_participants(participant_ids, tables)

    # Assert
    assert isinstance(rounds, dict), "Expected a dictionary for rounds allocation."
    seen_groups: Set[Tuple[int, ...]] = set()
    for round_allocation in rounds.values():
        for table in tables:
            table_participants: Tuple[int, ...] = tuple(sorted(round_allocation[table.id]))
            # Ensure group sizes are greater than 1 and that they have not been encountered before
            if table_participants and len(table_participants) > 1:
                assert table_participants not in seen_groups, f"Repeated group found: {table_participants}"
                seen_groups.add(table_participants)


def test_allocate_participants_simulation() -> None:
    """
    Test simulate_only mode to calculate the minimum number of rounds needed to encounter all unique groupings.
    """
    # Arrange
    total_participants: int = 16
    seats_per_table: int = 4
    table_quantity: int = 4
    tables: List[Table] = [Table(id=i, seats=seats_per_table) for i in range(1, table_quantity + 1)]

    # Act
    rounds_needed = allocate_participants(
        participants=list(range(1, total_participants + 1)), tables=tables, simulate_only=True
    )

    # Assert
    assert isinstance(rounds_needed, int), "Expected an integer as rounds needed in simulation mode."
    assert rounds_needed > 0, "Expected more than zero rounds needed for unique groupings."


@pytest.mark.parametrize("table_quantity, seats_per_table", [(2, 2), (3, 2), (2, 3)])
def test_allocate_participants_basic(table_quantity: int, seats_per_table: int) -> None:
    """
    Test basic allocation of participants to tables to ensure correct seating capacity is observed.
    """
    # Arrange
    tables: List[Table] = [Table(id=i, seats=seats_per_table) for i in range(1, table_quantity + 1)]
    participants: List[int] = list(range(1, table_quantity * seats_per_table + 1))

    # Act
    rounds = allocate_participants(participants, tables)

    # Assert
    assert isinstance(rounds, dict), "Expected a dictionary for rounds allocation."
    for round_allocation in rounds.values():
        for table in tables:
            assigned_participants: List[int] = round_allocation[table.id]
            assert len(assigned_participants) <= table.seats, "Exceeded seats per table"

    for round_allocation in rounds.values():
        all_assigned: List[int] = sum(round_allocation.values(), [])
        assert len(all_assigned) == len(set(all_assigned)), "Repeated participants in a single round"
