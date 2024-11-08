# src/services/participant_service.py
from typing import List

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from src.models.event import Event
from src.models.participant import Participant
from src.schemas.participant import ParticipantCreate, ParticipantRead


async def create_participant(participant_data: ParticipantCreate, db: Session) -> ParticipantRead:
    """
    Registers a new participant in the database if the event exists and there are no duplicates.

    Args:
        participant_data (ParticipantCreate): Data required to create a participant.
        db (Session): Database session object.

    Returns:
        ParticipantRead: The created participant's information.

    Raises:
        HTTPException: If a duplicate participant exists or if the event_id is invalid.
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


async def get_participant_by_id(participant_id: int, db: Session) -> ParticipantRead:
    """
    Fetch a participant by their unique ID.

    Parameters:
        participant_id (int): The ID of the participant.
        db (Session): The database session to perform the query.

    Returns:
        ParticipantRead: The participant data if found, else None.
    """
    return db.query(Participant).filter(Participant.id == participant_id).first()


async def get_all_participants(db: Session) -> List[ParticipantRead]:
    """
    Retrieve all participants stored in the database.

    Parameters:
        db (Session): The database session to perform the query.

    Returns:
        List[ParticipantRead]: A list of all participants.
    """
    return db.query(Participant).all()


async def update_participant(participant_id: int, participant_data: ParticipantCreate, db: Session) -> ParticipantRead:
    """
    Updates an existing participant's information based on their unique identifier.

    Args:
        participant_id (int): ID of the participant to update.
        participant_data (ParticipantCreate): Updated participant data.
        db (Session): Database session object.

    Returns:
        ParticipantRead: Updated participant information, or None if not found.

    Raises:
        HTTPException: If an unexpected error occurs during the update process.
    """
    participant = db.query(Participant).filter(Participant.id == participant_id).first()
    if not participant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Participant not found")
    for key, value in participant_data.model_dump().items():
        setattr(participant, key, value)
    try:
        db.commit()
        db.refresh(participant)
        return ParticipantRead.model_validate(participant)
    except Exception as e:
        db.rollback()
        print("Unexpected Error:", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {str(e)}"
        )


async def delete_participant(participant_id: int, db: Session) -> bool:
    """
    Delete a participant by their ID from the database.

    Parameters:
        participant_id (int): The ID of the participant to delete.
        db (Session): The database session to perform the delete operation.

    Returns:
        bool: True if the participant was deleted, False if not found.
    """
    participant = db.query(Participant).filter(Participant.id == participant_id).first()
    if not participant:
        return False
    db.delete(participant)
    db.commit()
    return True
