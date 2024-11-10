# src/routers/participants.py
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from src.database import get_db
from src.schemas.participant import (
    ParticipantCreate,
    ParticipantPaginatedResponse,
    ParticipantRead,
)
from src.services.participant_service import (
    create_participant,
    delete_participant,
    filter_participants,
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
    "/api/participants/",
    status_code=status.HTTP_200_OK,
    response_model=ParticipantPaginatedResponse,
    summary="Get all participants with pagination",
    responses={
        200: {
            "description": "List of participants returned successfully",
            "content": {
                "application/json": {
                    "example": {
                        "items": [
                            {
                                "id": 1,
                                "full_name": "John Doe",
                                "company_name": "Tech Corp",
                                "whatsapp": "+5511998765432",
                                "email": "johndoe@example.com",
                                "custom_data": {"additional_info": "Special requirements"},
                            },
                            {
                                "id": 2,
                                "full_name": "Jane Smith",
                                "company_name": "Business Inc",
                                "whatsapp": "+5511987654321",
                                "email": "janesmith@example.com",
                                "custom_data": {"additional_info": "Vegetarian meal"},
                            },
                        ],
                        "total_items": 50,
                        "total_pages": 5,
                        "current_page": 1,
                        "page_size": 10,
                    }
                }
            },
        },
        400: {"description": "Bad Request"},
        404: {"description": "Participants not found"},
    },
)
async def read_participants_route(
    db: Session = Depends(get_db),
    limit: int = Query(10, ge=1, description="Limit the number of results", examples=5),
    offset: int = Query(0, ge=0, description="The starting index of results", examples=0),
) -> ParticipantPaginatedResponse:
    """
    Retrieves a paginated list of participants.

    Parameters:
        db (Session): Database session dependency.
        limit (int): Maximum number of participants to return.
        offset (int): Starting index for pagination.

    Returns:
        ParticipantPaginatedResponse: A paginated list of participants.
    """
    filter_results = await get_all_participants(db, limit=limit, offset=offset)

    return ParticipantPaginatedResponse(
        items=[ParticipantRead.model_validate(participant) for participant in filter_results["participants"]],
        total_items=filter_results["total_records"],
        total_pages=filter_results["total_pages"],
        current_page=(offset // limit) + 1,
        page_size=limit,
    )


@router.get(
    "/api/participants/filter",
    status_code=status.HTTP_200_OK,
    response_model=ParticipantPaginatedResponse,
    summary="Get participants with filters",
    responses={
        200: {
            "description": "Filtered list of participants returned successfully",
            "content": {
                "application/json": {
                    "example": {
                        "items": [
                            {
                                "id": 1,
                                "full_name": "John Doe",
                                "company_name": "Tech Corp",
                                "whatsapp": "+5511998765432",
                                "email": "johndoe@example.com",
                                "custom_data": {"additional_info": "Special requirements"},
                            },
                        ],
                        "total_items": 50,
                        "total_pages": 5,
                        "current_page": 1,
                        "page_size": 10,
                    }
                }
            },
        },
        400: {"description": "Bad Request"},
        404: {"description": "No participants found"},
    },
)
async def filter_participants_route(
    db: Session = Depends(get_db),
    full_name: Optional[str] = Query(
        None, description="Full name of the participant", examples={"example": "Jane Doe"}
    ),
    company_name: Optional[str] = Query(
        None, description="Company name of the participant", examples={"example": "Tech Solutions Inc."}
    ),
    whatsapp: Optional[str] = Query(
        None, description="WhatsApp number of the participant", examples={"example": "+5511998765432"}
    ),
    email: Optional[str] = Query(
        None, description="Email of the participant", examples={"example": "jane.doe@example.com"}
    ),
    event_id: Optional[int] = Query(None, description="Event ID to filter participants by", examples={"example": 1}),
    limit: int = Query(10, ge=1, description="Limit the number of results", examples=5),
    offset: int = Query(0, ge=0, description="The starting index of results", examples=0),
) -> ParticipantPaginatedResponse:
    """
    Retrieve a list of participants based on the provided filters, with pagination.

    This route allows you to filter participants by different criteria, such as full name,
    company name, WhatsApp, email, and event ID, and supports pagination to limit the results.

    Args:
        db (Session): The database session dependency.
        full_name (str, optional): The full name of the participant to filter by.
        company_name (str, optional): The company name of the participant to filter by.
        whatsapp (str, optional): The WhatsApp number of the participant to filter by.
        email (str, optional): The email of the participant to filter by.
        event_id (int, optional): The event ID to filter participants by.
        limit (int): The maximum number of participants to return. Default is 10.
        offset (int): The starting index for pagination. Default is 0.

    Returns:
        ParticipantPaginatedResponse: A paginated list of participants matching the filter criteria,
        including the total number of items, total pages, current page, and page size.

    Raises:
        HTTPException: If the database query fails or no participants are found.
    """
    filter_results = await filter_participants(
        full_name=full_name,
        company_name=company_name,
        whatsapp=whatsapp,
        email=email,
        event_id=event_id,
        db=db,
        limit=limit,
        offset=offset,
    )

    return ParticipantPaginatedResponse(
        items=[ParticipantRead.model_validate(participant) for participant in filter_results["participants"]],
        total_items=filter_results["total_records"],
        total_pages=filter_results["total_pages"],
        current_page=(offset // limit) + 1,
        page_size=limit,
    )


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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Participant not found")
    return participant


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
