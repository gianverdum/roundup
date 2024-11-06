# src/schemas/table.py
from pydantic import BaseModel, ConfigDict, Field


class TableCreate(BaseModel):
    """
    Schema for creating multiple tables associated with an event.

    Attributes:
        event_id (int): ID of the event to which the table is linked.
        seats (int): Number of seats for each table (minimum 1).
        quantity (int): Number of tables to be created.
    """

    event_id: int
    seats: int = Field(..., ge=1)
    quantity: int = Field(..., ge=1)

    model_config = ConfigDict(from_attributes=True)


class TableResponse(TableCreate):
    """
    Response schema for a table including its ID.

    Attributes:
        id (int): Unique identifier of the table.
    """

    id: int
