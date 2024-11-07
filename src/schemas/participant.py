# src/schemas/participant.py
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import field_validate


class ParticipantCreate(BaseModel):
    """
    Schema for creating a participant with necessary details.

    Attributes:
        full_name (str): Full name of the participant.
        company_name (str): Company the participant is representing.
        whatsapp (str): Participant's WhatsApp number.
        email (str): Participant's email address.
        custom_data (dict, optional): Additional dynamic fields for the event.
        event_id (int): ID of the event the participant is attending.
    """

    full_name: str
    company_name: str
    whatsapp: str
    email: str
    custom_data: Optional[Dict[str, Any]] = Field(default=None)
    event_id: int

    model_config = ConfigDict(from_attributes=True)

    @field_validate("custom_data")
    def validate_custom_data(self, key: str, value: Optional[str]) -> Optional[str]:
        """
        Ensures that custom_data is stored as a string. If custom_data is not a string,
        it converts it to one. Returns None if the value is empty.
        """
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
