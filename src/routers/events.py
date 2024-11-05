# src/routers/events.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.database import get_db
from src.models.event import Event
from src.schemas.event import EventCreate, EventRead

router = APIRouter()


@router.post(
    "/events/",
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
async def create_event(event: EventCreate, db: Session = Depends(get_db)) -> EventRead:
    """
    Creates a new event.

    Parameters:
        event (EventCreate): The details of the event to be created.
        db (Session): Database session dependency.

    Returns:
        EventRead: The newly created event record.

    Raises:
        HTTPException: If an error occurs during event creation.
    """
    # Create the db_event instance using the EventCreate data
    db_event = Event(**event.model_dump())

    try:
        db.add(db_event)
        db.commit()
        db.refresh(db_event)
        return EventRead.model_validate(db_event)
    except IntegrityError as e:
        db.rollback()
        print("Integrity Error:", e)  # Debugging output
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Event with the same name and date already exists."
        )
    except Exception as e:
        db.rollback()
        print("Unexpected Error:", e)  # Debugging output
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {str(e)}"
        )
