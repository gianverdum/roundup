# src/services/event_service.py
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.models.event import Event
from src.schemas.event import EventCreate, EventRead


async def create_event(event: EventCreate, db: Session) -> EventRead:
    """
    Creates a new event in the database.

    Parameters:
        event (EventCreate): The details of the event to be created.
        db (Session): Database session dependency.

    Returns:
        EventRead: The newly created event record.

    Raises:
        HTTPException: If an error occurs during event creation.
    """
    db_event = Event(**event.model_dump())

    try:
        db.add(db_event)
        db.commit()
        db.refresh(db_event)
        return EventRead.model_validate(db_event)
    except IntegrityError as e:
        db.rollback()
        print("Integrity Error:", e)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Event with the same name and date already exists."
        )
    except Exception as e:
        db.rollback()
        print("Unexpected Error:", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {str(e)}"
        )
