# src/services/allocation_service.py
from typing import Dict, List, Union

from src.models.table import Table


def allocate_participants(
    participants: List[int], tables: List[Table], simulate_only: bool = False
) -> Union[Dict[int, Dict[int, List[int]]], int]:
    """
    Allocate participants across rounds using a controlled transposition approach,
    ensuring unique groupings based on the Excel approach.

    Parameters:
        - participants (List[int]): List of participant IDs.
        - tables (List[Table]): List of table configurations.
        - simulate_only (bool): If True, only returns the number of rounds needed.

    Returns:
        Union[Dict[int, Dict[int, List[int]]], int]: A dictionary of rounds with table allocations or
        the count of rounds if in simulate_only mode.
    """
    rounds = {}
    num_tables = len(tables)
    table_capacity = tables[0].seats  # Assume all tables have the same capacity

    # Step 1: Create the initial allocation (first round)
    initial_allocation = {
        tables[i].id: participants[i * table_capacity : (i + 1) * table_capacity] for i in range(num_tables)
    }
    rounds[1] = initial_allocation

    # Step 2: Generate subsequent rounds by rotating participant positions
    round_number = 2
    current_allocation = initial_allocation

    while True:
        new_allocation: Dict[int, List[int]] = {table.id: [] for table in tables}
        column_index = 0  # To track current column position for transposition

        # Transpose the previous round's matrix into the new round's matrix
        for row in current_allocation.values():
            remaining_positions = table_capacity - len(new_allocation[tables[column_index].id])

            # Fill the current column with as many participants as fit
            for i in range(len(row)):
                if remaining_positions == 0:
                    # Move to the next column if the current one is full
                    column_index += 1
                    remaining_positions = table_capacity

                new_allocation[tables[column_index].id].append(row[i])
                remaining_positions -= 1

                if column_index >= num_tables:
                    break  # Ensure we don't exceed the table limit in rare edge cases

        # Check if the allocation is repeating the initial allocation, which means we're done
        if new_allocation == initial_allocation:
            # Return only the count if in simulation mode
            if simulate_only:
                return round_number - 1
            break

        rounds[round_number] = new_allocation
        current_allocation = new_allocation
        round_number += 1

    # Return the full allocation plan across all rounds if not in simulation mode
    return rounds
