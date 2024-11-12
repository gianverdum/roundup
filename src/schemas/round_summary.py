# src/schemas/round_summary.py
from typing import List

from pydantic import BaseModel, ConfigDict


class TableAllocationSummary(BaseModel):
    """
    Summary of participants allocated to a specific table in a round.

    Attributes:
        table_id (int): ID of the table.
        participant_ids (List[int]): List of participant IDs allocated to the table.
    """

    table_id: int
    participant_ids: List[int]


class RoundSummary(BaseModel):
    """
    Summary of a round with table allocations.

    Attributes:
        round_number (int): Number of the round.
        allocations (List[TableAllocationSummary]): List of allocations per table in the round.
    """

    round_number: int
    allocations: List[TableAllocationSummary]

    model_config = ConfigDict(from_attributes=True)
