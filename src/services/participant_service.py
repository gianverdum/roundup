from fastapi import HTTPException, status
from sqlalchemy.orm import Session

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
    """
    existing_participant = (
        db.query(Participant)
        .filter((Participant.email == participant_data.email) | (Participant.whatsapp == participant_data.whatsapp))
        .first()
    )
    if existing_participant:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="A participant with the same email or WhatsApp already exists."
        )

    db_participant = Participant(**participant_data.model_dump())

    db.add(db_participant)
    db.commit()
    db.refresh(db_participant)

    return ParticipantRead.model_validate(db_participant)
