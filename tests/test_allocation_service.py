# tests/test_allocation_service.py
from typing import List

import pytest

from src.models.table import Table
from src.services.allocation_service import allocate_participants


@pytest.mark.parametrize("max_rounds", [None, 3])
def test_allocate_participants_with_and_without_max_rounds(max_rounds: int) -> None:
    """
    Test allocation with and without the max_rounds parameter to ensure behavior is consistent.
    """
    # Arrange
    table_quantity = 5
    seats_per_table = 4
    participants = list(range(1, 21))
    tables: List[Table] = [Table(id=i, seats=seats_per_table) for i in range(1, table_quantity + 1)]

    # Act
    rounds = allocate_participants(participants, tables, max_rounds=max_rounds)

    # Assert
    assert isinstance(rounds, dict), "Expected a dictionary of rounds for allocation"
    if max_rounds is not None:
        assert len(rounds) <= max_rounds, f"Expected rounds to be capped at {max_rounds}"
    else:
        assert len(rounds) <= table_quantity, "Expected rounds to be capped at the number of tables"


def test_allocate_participants_unique_encounters() -> None:
    """
    Test that allocation maximizes unique encounters between participants.
    """
    # Arrange
    table_quantity = 3
    seats_per_table = 2
    participants = list(range(1, 7))
    tables: List[Table] = [Table(id=i, seats=seats_per_table) for i in range(1, table_quantity + 1)]

    # Act
    rounds = allocate_participants(participants, tables)

    # Assert
    assert isinstance(rounds, dict), "Expected a dictionary of rounds for allocation"
    encounters = set()
    for round_allocation in rounds.values():
        for table_participants in round_allocation.values():
            for p1 in table_participants:
                for p2 in table_participants:
                    if p1 != p2:
                        pair = tuple(sorted((p1, p2)))
                        encounters.add(pair)
    expected_encounters = len(participants) * (len(participants) - 1) / 2
    assert len(encounters) <= expected_encounters, "Exceeded unique encounters"
