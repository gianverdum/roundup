# src/schemas/event.py
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class EventCreate(BaseModel):
    """
    Schema for creating a new event.

    Attributes:
        name (str): Name of the event with minimum character requirement.
        date (datetime): Date and time for the event, validated format.
        location (str): Location of the event with minimum character requirement.
        participant_limit (int): Limit for number of participants, must be greater than 0.
        address (str): Address of the event, required to have specific characteristics.
        max_seats_per_table (int): Maximum number of seats allowed per table for the event.
        tables_count (int): Number of tables to be created for the event.
    """

    name: str = Field(..., min_length=3, max_length=100, description="Name of the event, at least 3 characters.")
    date: datetime = Field(..., description="Date and time for the event, must be in correct datetime format.")
    location: str = Field(
        ..., min_length=3, max_length=100, description="Location of the event, at least 3 characters."
    )
    address: str = Field(
        ..., min_length=10, max_length=200, description="Address of the event, must be a full address."
    )
    participant_limit: int = Field(..., gt=0, description="Limit for number of participants, must be greater than 0.")
    max_seats_per_table: int = Field(..., gt=1, description="2 is the minimum number of seats allowed per table.")
    tables_count: int = Field(..., gt=0, description="1 is the minimun number of tables to be created for the event.")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "name": "Annual Business Round",
                "date": "2024-12-05T15:30:00",
                "location": "Business Center, São Paulo",
                "address": "Av. Paulista, 1000 - Bela Vista, São Paulo - SP, 01310-000",
                "participant_limit": 50,
                "max_seats_per_table": 8,
                "tables_count": 12,
            }
        },
    )

    @field_validator("date")
    def date_not_in_past(cls, value: datetime) -> datetime:
        if value < datetime.now():
            raise ValueError("The event date cannot be in the past.")
        return value


class EventRead(EventCreate):
    """
    Schema for reading an event, which includes the event ID.

    Attributes:
        id (int): Unique identifier for the event.
        name (str): Name of the event.
        date (datetime): Date and time of the event.
        location (str): Location of the event.
        participant_limit (int): Limit for number of participants.
        address (str): Address of the event.
        max_seats_per_table (int): Maximum number of seats per table for the event.
        tables_count (int): Number of tables created for the event.
    """

    id: int

    model_config = ConfigDict(from_attributes=True)
