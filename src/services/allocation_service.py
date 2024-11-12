# src/services/allocation_service.py
import random
from math import ceil
from typing import Dict, List, Optional, Set, Tuple

from src.models.table import Table


def calculate_rounds_needed(total_participants: int, seats_per_table: int, table_count: int) -> int:
    """Calculate the minimum rounds needed for participants to interact uniquely."""
    seats_per_round = seats_per_table * table_count
    if total_participants <= seats_per_round:
        return 1
    groups_needed = total_participants // seats_per_table
    return ceil(groups_needed / table_count)


def allocate_participants(
    participants: List[int], tables: List[Table], max_rounds: Optional[int] = None
) -> Dict[int, Dict[int, List[int]]]:
    """
    Allocate participants across rounds, ensuring unique pairings.
    """
    table_count = len(tables)
    required_rounds = calculate_rounds_needed(len(participants), tables[0].seats, table_count)
    max_rounds = max_rounds or required_rounds

    rounds = {}
    round_number = 1
    possible_pairs: Set[Tuple[int, int]] = {
        (min(a, b), max(a, b)) for i, a in enumerate(participants) for b in participants[i + 1 :]
    }
    encountered_pairs: Set[Tuple[int, int]] = set()

    while encountered_pairs != possible_pairs and round_number <= max_rounds:
        round_allocation: Dict[int, List[int]] = {table.id: [] for table in tables}
        shuffled_participants = participants[:]
        random.shuffle(shuffled_participants)

        for table in tables:
            assigned: List[int] = []
            while len(assigned) < table.seats and shuffled_participants:
                candidate = shuffled_participants.pop(0)
                if all((min(candidate, other), max(candidate, other)) not in encountered_pairs for other in assigned):
                    assigned.append(candidate)

            round_allocation[table.id] = assigned
            for i, p1 in enumerate(assigned):
                for p2 in assigned[i + 1 :]:
                    encountered_pairs.add((min(p1, p2), max(p1, p2)))

        rounds[round_number] = round_allocation
        round_number += 1

    if encountered_pairs != possible_pairs:
        print("Warning: Unable to complete unique pairings within the maximum rounds allowed.")

    for rnd, allocation in rounds.items():
        print(f"\nRound {rnd}:")
        for table_id, seated_participants in allocation.items():
            print(f"  Table {table_id}: Participants {seated_participants}")

    return rounds
