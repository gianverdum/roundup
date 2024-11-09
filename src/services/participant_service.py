# src/services/participant_service.py
from math import ceil
from typing import Any, Dict, Optional

from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
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


async def get_all_participants(db: Session, limit: int, offset: int) -> Dict[str, Any]:
    """
    Retrieves a paginated list of all participants with the total number of records and pages.

    Parameters:
        db (Session): Database session dependency.
        limit (int): Maximum number of participants to return.
        offset (int): Starting index for pagination.

    Returns:
        Dict[str, Any]: A dictionary compatible with ParticipantPaginatedResponse.
    """
    try:
        total_records = db.query(Participant).count()
        participants = db.query(Participant).offset(offset).limit(limit).all()

        return {
            "total_records": total_records,
            "total_pages": ceil(total_records / limit),
            "participants": participants,
        }

    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=500, detail="Database query failed. Please check the database connection or query logic."
        ) from e


async def filter_participants(
    full_name: Optional[str],
    company_name: Optional[str],
    whatsapp: Optional[str],
    email: Optional[str],
    event_id: Optional[int],
    db: Session,
    limit: int,
    offset: int,
) -> Dict[str, Any]:
    """
    Filters and paginates participants based on optional parameters.

    This function performs a query to filter participants by the specified criteria (full name, company name,
    WhatsApp, email, event ID, and custom data) and returns a paginated list of results.

    Args:
        full_name (str, optional): The full name of the participant to filter by.
        company_name (str, optional): The company name of the participant to filter by.
        whatsapp (str, optional): The WhatsApp number of the participant to filter by.
        email (str, optional): The email of the participant to filter by.
        db (Session): The database session dependency.
        limit (int): The maximum number of participants to return.
        offset (int): The starting index for pagination.

    Returns:
        Dict[str, Any]: A dictionary containing the filtered list of participants, the total records,
        and the total number of pages based on the provided pagination.

    Raises:
        HTTPException: If the database connection fails, or no participants match the filter criteria.
    """
    try:
        query = db.query(Participant)

        if full_name:
            query = query.filter(Participant.full_name.ilike(f"%{full_name}%"))
        if company_name:
            query = query.filter(Participant.company_name.ilike(f"%{company_name}%"))
        if whatsapp:
            query = query.filter(Participant.whatsapp.ilike(f"%{whatsapp}%"))
        if email:
            query = query.filter(Participant.email.ilike(f"%{email}%"))
        if event_id:
            query = query.filter(Participant.event_id == event_id)

        total_records = query.count()
        participants = query.offset(offset).limit(limit).all()

        if not participants:
            raise HTTPException(status_code=404, detail="No participants found matching the filter criteria.")

        return {
            "total_records": total_records,
            "total_pages": ceil(total_records / limit),
            "participants": participants,
        }

    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=500, detail="Database connection failed or there was an error processing the request."
        ) from e


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
