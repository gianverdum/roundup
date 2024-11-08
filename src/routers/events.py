# src/routers/events.py
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from src.database import get_db
from src.schemas.event import EventCreate, EventRead
from src.services.event_service import (
    create_event,
    delete_event,
    get_all_events,
    get_event_by_id,
    update_event,
)

router = APIRouter()


@router.post(
    "/api/events/",
    response_model=EventRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register the event",
    responses={
        201: {
            "description": "Event created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "name": "Annual Business Round",
                        "date": "2024-12-05T15:30:00",
                        "location": "Business Center, São Paulo",
                        "address": "Av. Paulista, 1000 - Bela Vista, São Paulo - SP, 01310-000",
                        "participant_limit": 50,
                        "max_seats_per_table": 8,
                        "tables_count": 12,
                    }
                }
            },
        },
        400: {"description": "Bad Request"},
        409: {"description": "Conflict - could not create event"},
    },
)
async def create_event_route(event: EventCreate, db: Session = Depends(get_db)) -> EventRead:
    """
    Handles the event creation route.

    Parameters:
        event (EventCreate): The details of the event to be created.
        db (Session): Database session dependency.

    Returns:
        EventRead: The newly created event record.
    """
    return await create_event(event, db)


@router.get(
    "/api/events/{event_id}",
    status_code=status.HTTP_200_OK,
    response_model=EventRead,
    summary="Get event by ID",
    responses={
        200: {"description": "Event returned successfully"},
        404: {"description": "Event not found"},
    },
)
async def read_event_route(event_id: int, db: Session = Depends(get_db)) -> EventRead:
    """
    Retrieves an event by its ID.

    Parameters:
        event_id (int): The unique identifier of the event.
        db (Session): Database session dependency.

    Returns:
        EventRead: The event details if found.

    Raises:
        HTTPException: If the event is not found.
    """
    event = await get_event_by_id(event_id, db)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    return event


@router.get(
    "/api/events/",
    status_code=status.HTTP_200_OK,
    response_model=List[EventRead],
    summary="Get all events",
    responses={200: {"description": "List of events returned successfully"}},
)
async def read_events_route(db: Session = Depends(get_db)) -> List[EventRead]:
    """
    Retrieves a list of all events.

    Parameters:
        db (Session): Database session dependency.

    Returns:
        List[EventRead]: A list of all events.
    """
    return await get_all_events(db)


@router.put(
    "/api/events/{event_id}",
    status_code=status.HTTP_200_OK,
    response_model=EventRead,
    summary="Update event",
    responses={
        200: {"description": "Event updated successfully"},
        404: {"description": "Event not found"},
    },
)
async def update_event_route(event_id: int, event_data: EventCreate, db: Session = Depends(get_db)) -> EventRead:
    """
    Updates an existing event's details.

    Parameters:
        event_id (int): The unique identifier of the event.
        event_data (EventCreate): The new data for the event.
        db (Session): Database session dependency.

    Returns:
        EventRead: The updated event details.

    Raises:
        HTTPException: If the event is not found.
    """
    updated_event = await update_event(event_id, event_data, db)
    if not updated_event:
        raise HTTPException(status_code=status.HTTP_404, detail="Event not found")
    return updated_event


@router.delete(
    "/api/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete event", response_class=Response
)
async def delete_event_route(event_id: int, db: Session = Depends(get_db)) -> None:
    """
    Deletes an event by its ID.

    Parameters:
        event_id (int): The unique identifier of the event.
        db (Session): Database session dependency.

    Returns:
        dict: Message indicating successful deletion.

    Raises:
        HTTPException: If the event is not found.
    """
    success = await delete_event(event_id, db)
    if not success:
        raise HTTPException(status_code=status.HTTP_404, detail="Event not found")
