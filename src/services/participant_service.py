from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from src.models.event import Event
from src.models.participant import Participant
from src.schemas.participant import ParticipantCreate, ParticipantRead


async def create_participant(participant_data: ParticipantCreate, db: Session) -> ParticipantRead:
    """
    Creates a new participant in the database.

    Args:
        participant_data (ParticipantCreate): The data for creating a participant.
        db (Session): The database session.

    Returns:
        ParticipantRead: The created participant.

    Raises:
        HTTPException: If a participant with the same email or WhatsApp exists or
                       if the event_id does not correspond to an existing event.
    """

    event_exists = db.query(Event).filter(Event.id == participant_data.event_id).first()
    if not event_exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Event with id {participant_data.event_id} does not exist."
        )

    existing_participant = (
        db.query(Participant)
        .filter(
            (Participant.email == participant_data.email) | (Participant.whatsapp == participant_data.whatsapp),
            Participant.event_id == participant_data.event_id,
        )
        .first()
    )

    if existing_participant:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A participant with this email or whatsapp is already registered for this event.",
        )

    db_participant = Participant(**participant_data.model_dump())

    db.add(db_participant)
    db.commit()
    db.refresh(db_participant)

    return ParticipantRead.model_validate(db_participant)
