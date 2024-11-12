# src/schemas/table_allocation.py
from pydantic import BaseModel, ConfigDict


class TableAllocationCreate(BaseModel):
    """
    Schema for creating a new table allocation in a specific round.

    Attributes:
        round_id (int): ID of the round associated with this allocation.
        table_id (int): ID of the table where the participant is allocated.
        participant_id (int): ID of the participant allocated to the table.
    """

    round_id: int
    table_id: int
    participant_id: int

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={"example": {"round_id": 1, "table_id": 2, "participant_id": 101}},
    )


class TableAllocationRead(TableAllocationCreate):
    """
    Schema for reading an existing table allocation, including its unique ID.

    Attributes:
        id (int): Unique identifier for the table allocation.
    """

    id: int

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={"example": {"id": 1, "round_id": 1, "table_id": 2, "participant_id": 101}},
    )
