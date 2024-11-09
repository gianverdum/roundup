# src/routers/events.py
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from src.database import get_db
from src.schemas.event import EventCreate, EventPaginatedResponse, EventRead
from src.services.event_service import (
    create_event,
    delete_event,
    filter_events,
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
    "/api/events/",
    status_code=status.HTTP_200_OK,
    response_model=Dict[str, Any],
    summary="Get all events with pagination",
    responses={
        200: {
            "description": "List of paginated events returned successfully",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": 1,
                            "name": "Annual Meetup",
                            "date": "2024-12-01T14:00:00",
                            "location": "New York",
                            "participant_limit": 100,
                            "max_seats_per_table": 10,
                        },
                        {
                            "id": 2,
                            "name": "Tech Conference",
                            "date": "2024-11-20T10:00:00",
                            "location": "San Francisco",
                            "participant_limit": 200,
                            "max_seats_per_table": 8,
                        },
                    ]
                }
            },
        }
    },
)
async def read_events_route(
    db: Session = Depends(get_db),
    limit: int = Query(10, ge=1, description="Limit the number of results", example=5),
    offset: int = Query(0, ge=0, description="The starting index of results", example=0),
) -> Dict[str, Any]:
    """
    Retrieves a paginated list of all events with total records and pages.

    Parameters:
        db (Session): Database session dependency.
        limit (int): Maximum number of events to return.
        offset (int): Starting index for pagination.

    Returns:
        Dict[str, Any]: A dictionary containing the list of events, total records, and total pages.
    """
    return await get_all_events(db, limit=limit, offset=offset)


@router.get(
    "/api/events/filter",
    status_code=status.HTTP_200_OK,
    response_model=EventPaginatedResponse,
    summary="Filter events with pagination",
    responses={
        200: {
            "description": "Filtered and paginated list of events returned successfully",
            "content": {
                "application/json": {
                    "example": {
                        "items": [
                            {
                                "id": 1,
                                "name": "Annual Meetup",
                                "date": "2024-12-01T14:00:00",
                                "location": "New York",
                                "participant_limit": 100,
                                "max_seats_per_table": 10,
                            }
                        ],
                        "total_items": 1,
                        "total_pages": 1,
                        "current_page": 1,
                        "page_size": 10,
                    }
                }
            },
        },
        404: {
            "description": "No events found matching the filter criteria.",
        },
        500: {
            "description": "Database connection failed or error in request processing.",
        },
    },
)
async def filter_events_route(
    name: Optional[str] = Query(None, description="Filter by event name", example="Tech Conference"),
    date: Optional[datetime] = Query(None, description="Filter by event date", example="2024-11-20T10:00:00"),
    location: Optional[str] = Query(None, description="Filter by event location", example="San Francisco"),
    participant_limit: Optional[int] = Query(None, description="Filter by participant limit", example=200),
    max_seats_per_table: Optional[int] = Query(None, description="Filter by max seats per table", example=8),
    db: Session = Depends(get_db),
    limit: int = Query(10, ge=1, description="Limit the number of results", example=5),
    offset: int = Query(0, ge=0, description="The starting index of results", example=0),
) -> EventPaginatedResponse:
    """
    Retrieves a paginated list of events filtered by the provided parameters.

    Parameters:
        name (str, optional): Event name to filter by.
        date (datetime, optional): Event date to filter by.
        location (str, optional): Event location to filter by.
        participant_limit (int, optional): Limit of participants to filter by.
        max_seats_per_table (int, optional): Max seats per table to filter by.
        db (Session): Database session dependency.
        limit (int): Maximum number of events to return.
        offset (int): Starting index for pagination.

    Returns:
        PaginatedResponse: A paginated list of events matching the filters.

    Raises:
        HTTPException: If no events are found or a database error occurs.
    """
    filter_results = await filter_events(
        name, date, location, participant_limit, max_seats_per_table, db, limit, offset
    )

    return EventPaginatedResponse(
        items=[EventRead.model_validate(event) for event in filter_results["events"]],
        total_items=filter_results["total_records"],
        total_pages=filter_results["total_pages"],
        current_page=(offset // limit) + 1,
        page_size=limit,
    )


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
