# src/schemas/event.py
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class EventCreate(BaseModel):
    """
    Schema for creating a new event.

    Attributes:
        name (str): Name of the event with minimum character requirement.
        date (datetime): Date and time for the event, validated format.
        location (str): Location of the event with minimum character requirement.
        participant_limit (int): Limit for number of participants, must be greater than 0.
        address (str): Address of the event, required to have specific characteristics.
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

    class ConfigDict:
        from_atributes = True
        json_schema_extra = {
            "example": {
                "name": "Annual Business Round",
                "date": "2024-12-05T15:30:00",
                "location": "Business Center, São Paulo",
                "address": "Av. Paulista, 1000 - Bela Vista, São Paulo - SP, 01310-000",
                "participant_limit": 50,
            }
        }

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
    """

    id: int

    class ConfigDict:
        from_atributes = True
