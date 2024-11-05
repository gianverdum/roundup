# src/routers/events.py
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from src.database import get_db
from src.schemas.event import EventCreate, EventRead
from src.services.event_service import create_event

router = APIRouter()


@router.post(
    "/api/events/",
    response_model=EventRead,
    status_code=status.HTTP_201_CREATED,
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
