# src/routers/participants.py
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from src.database import get_db
from src.schemas.participant import ParticipantCreate, ParticipantRead
from src.services.participant_service import (
    create_participant,
    delete_participant,
    get_all_participants,
    get_participant_by_id,
    update_participant,
)

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


@router.get(
    "/api/participants/{participant_id}",
    status_code=status.HTTP_200_OK,
    response_model=ParticipantRead,
    summary="Get participant by ID",
    responses={
        200: {
            "description": "Participant returned successfully",
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
        404: {"description": "Participant with the specified ID was not found"},
    },
)
async def read_participant_route(participant_id: int, db: Session = Depends(get_db)) -> ParticipantRead:
    """
    Retrieves a participant by their unique identifier.

    Parameters:
        - participant_id (int): The ID of the participant to retrieve.

    Returns:
        ParticipantRead: Information about the retrieved participant.

    Raises:
        HTTPException: If no participant is found with the provided ID.
    """
    participant = await get_participant_by_id(participant_id, db)
    if not participant:
        raise HTTPException(status_code=status.HTTP_404, detail="Participant not found")
    return participant


@router.get(
    "/api/participants/",
    status_code=status.HTTP_200_OK,
    response_model=List[ParticipantRead],
    summary="Get all participants",
    responses={
        200: {
            "description": "Participant's list returned successfully",
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
        404: {"description": "Participant not found"},
    },
)
async def read_participants_route(db: Session = Depends(get_db)) -> List[ParticipantRead]:
    """
    Retrieve a list of all registered participants in the database.

    Parameters:
        db (Session): The database session to perform the query.

    Returns:
        List[ParticipantRead]: A list of participants.

    Raises:
        HTTPException 400: If the request format is invalid.
        HTTPException 404: If no participants are found.
    """
    return await get_all_participants(db)


@router.put(
    "/api/participants/{participant_id}",
    status_code=status.HTTP_200_OK,
    response_model=ParticipantRead,
    summary="Update participant",
    responses={
        200: {
            "description": "Participant updated successfully",
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
        404: {"description": "Participant not found"},
    },
)
async def update_participant_route(
    participant_id: int, participant_data: ParticipantCreate, db: Session = Depends(get_db)
) -> ParticipantRead:
    """
    Update an existing participant's information in the database.

    Parameters:
        participant_id (int): The ID of the participant to be updated.
        participant_data (ParticipantCreate): The data to update the participant with.
        db (Session): The database session to perform the query.

    Returns:
        ParticipantRead: The updated participant information.

    Raises:
        HTTPException 404: If the participant is not found in the database.
        HTTPException 400: If the request data is invalid.
    """
    updated_participant = await update_participant(participant_id, participant_data, db)
    if not updated_participant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Participant not found")
    return updated_participant


@router.delete(
    "/api/participants/{participant_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete participant",
    response_class=Response,
)
async def delete_participant_route(participant_id: int, db: Session = Depends(get_db)) -> None:
    """
    Deletes a participant by their unique identifier.

    Parameters:
        - participant_id (int): The ID of the participant to delete.

    Returns:
        dict: Confirmation message indicating successful deletion.

    Raises:
        HTTPException: If no participant is found with the provided ID.
    """
    success = await delete_participant(participant_id, db)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Participant not found")
