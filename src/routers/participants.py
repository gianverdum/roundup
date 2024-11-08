# src/routers/participants.py
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from src.database import get_db
from src.schemas.participant import ParticipantCreate, ParticipantRead
from src.services.participant_service import create_participant

router = APIRouter()


@router.post(
    "/api/participants/",
    response_model=ParticipantRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register the Participant",
    responses={
        201: {
            "description": "Participant registered successfully",
            "content": {
                "application/json": {
                    "example": {
                        "full_name": "John Doe",
                        "company_name": "My business",
                        "whatsapp": "11911112222",
                        "email": "email@gmail.com",
                        "custom_data": {"preferences": {"theme": "dark", "notifications": True}},
                        "event_id": 1,
                    }
                }
            },
        },
        400: {"description": "Bad Request"},
        409: {"description": "Conflict - could not register participant"},
    },
)
async def create_participant_route(participant: ParticipantCreate, db: Session = Depends(get_db)) -> ParticipantRead:
    """
    Creates a new participant and associates them with a specific event.

    Parameters:
        - full_name (str): Full name of the participant.
        - company_name (str): Company the participant is representing.
        - whatsapp (str): Participant's WhatsApp number.
        - email (str): Participant's email address.
        - custom_data (dict, optional): Additional dynamic fields specific to the event.
        - event_id (int): ID of the associated event.

    Returns:
        ParticipantRead: Information about the newly created participant.

    Raises:
        HTTPException: If a participant with the same email or WhatsApp exists.
    """

    return await create_participant(participant, db)
