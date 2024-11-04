# src/routers/events.py
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from src.database import get_db
from src.models.event import Event
from src.schemas.event import EventCreate

router = APIRouter()


@router.post(
    "/events/",
    response_model=EventCreate,
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
    },
)
def create_event(event: EventCreate, db: Session = Depends(get_db)) -> Event:
    """
    Creates a new event.

    Parameters:
        event (EventCreate): The details of the event to be created.
        db (Session): Database session dependency.

    Returns:
        Event: The newly created event record.

    Raises:
        HTTPException: If an error occurs during event creation.
    """
    db_event = Event(**event.model_dump())
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event
