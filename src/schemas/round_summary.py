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

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={"example": {"table_id": 1, "participant_ids": [101, 102, 103]}},
    )


class RoundSummary(BaseModel):
    """
    Summary of a round with table allocations.

    Attributes:
        round_number (int): Number of the round.
        allocations (List[TableAllocationSummary]): List of allocations per table in the round.
    """

    round_number: int
    allocations: List[TableAllocationSummary]

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "round_number": 1,
                "allocations": [
                    {"table_id": 1, "participant_ids": [101, 102, 103]},
                    {"table_id": 2, "participant_ids": [104, 105, 106]},
                ],
            }
        },
    )
