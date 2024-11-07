# src/schemas/table.py
from pydantic import BaseModel, ConfigDict, Field, field_validator


class TableCreate(BaseModel):
    """
    Schema for creating multiple tables associated with an event.

    Attributes:
        event_id (int): ID of the event to which the table is linked.
        seats (int): Number of seats for each table (minimum 1).
        quantity (int): Number of tables to be created.
    """

    event_id: int
    seats: int = Field(..., ge=2)
    quantity: int = Field(..., ge=1)

    model_config = ConfigDict(from_attributes=True)

    @field_validator("seats")
    def check_seats(cls, value: int) -> int:
        if not isinstance(value, int):
            raise ValueError("Seats must be an integer.")
        return value

    @field_validator("quantity")
    def check_quantity(cls, value: int) -> int:
        if not isinstance(value, int):
            raise ValueError("Quantity must be an integer.")
        return value


class TableResponse(BaseModel):
    """
    Response schema for a table including its ID.

    Attributes:
        id (int): Unique identifier of the table.
    """

    id: int
    event_id: int
    table_number: int
    seats: int
