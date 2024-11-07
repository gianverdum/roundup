# src/schemas/participant.py
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import field_validate


class ParticipantCreate(BaseModel):
    full_name: str
    company_name: str
    whatsapp: str
    email: str
    custom_data: Optional[Dict[str, Any]] = Field(default=None)

    model_config = ConfigDict(from_attributes=True)

    @field_validate("custom_data")
    def validate_custom_data(self, key: str, value: Optional[str]) -> Optional[str]:
        return value if isinstance(value, str) else str(value) if value is not None else None


class ParticipantRead(ParticipantCreate):
    """
    Schema for reading a participant, which includes the participant ID.

    Attributes:
        id (int): Unique identifier for the participant.
        full_name (str): Name of the participant.
        whatsapp (str): Whatsapp of the participant.
        email (str): E-mail of the participant.
        custom_data (Dict): Additional dynamic fields specific to the event (optional).
    """

    id: int

    model_config = ConfigDict(from_attributes=True)
