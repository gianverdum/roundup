# src/schemas/table.py
from typing import List

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


class TablePaginatedResponse(BaseModel):
    """
    Schema for paginated response of tables.

    This schema is used to return a paginated list of tables with total count and pagination metadata.

    Attributes:
        items (List[TableResponse]): List of tables in the current page, serialized as TableResponse models.
        total_items (int): The total number of tables matching the filter criteria.
        total_pages (int): The total number of pages based on the pagination parameters.
        current_page (int): The current page number in the pagination.
        page_size (int): The number of items per page in the pagination.
    """

    items: List[TableResponse]
    total_items: int
    total_pages: int
    current_page: int
    page_size: int

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "items": [
                    {
                        "id": 1,
                        "event_id": 1,
                        "table_number": 1,
                        "seats": 8,
                    },
                    {
                        "id": 2,
                        "event_id": 1,
                        "table_number": 2,
                        "seats": 8,
                    },
                ],
                "total_items": 30,
                "total_pages": 3,
                "current_page": 1,
                "page_size": 10,
            }
        },
    )


class TableUpdate(BaseModel):
    """
    Schema for updating table details.

    Attributes:
        id (int): Unique identifier for the table.
        event_id (int): ID of the event to which the table is linked.
        table_number (int): Number identifying the table within the event.
        seats (int): Number of seats available at the table.
    """

    event_id: int
    table_number: int = Field(..., ge=1)
    seats: int = Field(..., ge=2)

    model_config = ConfigDict(from_attributes=True)
