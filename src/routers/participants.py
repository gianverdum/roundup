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
                        "custom_data": "JSON",
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
    Create a new participant and associate them with the event.
    The custom data allows dynamic attributes based on event needs.

    - **full_name**: Full name of the participant.
    - **company_name**: Company the participant is representing.
    - **whatsapp**: Participant's WhatsApp number.
    - **email**: Participant's email address.
    - **custom_data**: Additional dynamic fields specific to the event (optional).
    """
    return await create_participant(participant, db)
