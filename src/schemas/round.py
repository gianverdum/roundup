# src/schemas/round.py
from pydantic import BaseModel, ConfigDict, Field


class RoundCreate(BaseModel):
    """
    Schema for creating a new round associated with an event.

    Attributes:
        event_id (int): ID of the event for the round.
        round_number (int): Sequential number for the round in the event.
    """

    event_id: int
    round_number: int = Field(..., description="Sequential number of the round for the event")

    model_config = ConfigDict(from_attributes=True)


class RoundRead(RoundCreate):
    """
    Schema for reading an existing round, including its ID.

    Attributes:
        id (int): Unique ID for the round.
    """

    id: int

    model_config = ConfigDict(from_attributes=True)
