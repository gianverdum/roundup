# src/services/event_service.py
from typing import List

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
        HTTPException: If an IntegrityError occurs or another error prevents creation.
    """
    existing_event = db.query(Event).filter_by(name=event.name, date=event.date).first()

    if existing_event:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Event with the same name and date already exists."
        )

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


async def get_event_by_id(event_id: int, db: Session) -> EventRead:
    """
    Retrieves an event by its ID.

    Parameters:
        event_id (int): The unique identifier of the event.
        db (Session): Database session dependency.

    Returns:
        EventRead: The event details if found, None otherwise.
    """
    return db.query(Event).filter(Event.id == event_id).first()


async def get_all_events(db: Session) -> List[EventRead]:
    """
    Retrieves a list of all events.

    Parameters:
        db (Session): Database session dependency.

    Returns:
        List[EventRead]: A list of all event records.
    """
    return db.query(Event).all()


async def update_event(event_id: int, event_data: EventCreate, db: Session) -> EventRead:
    """
    Updates an existing event's details.

    Parameters:
        event_id (int): The unique identifier of the event.
        event_data (EventCreate): The new data for the event.
        db (Session): Database session dependency.

    Returns:
        EventRead: The updated event details.

    Raises:
        HTTPException: If an error occurs during update.
    """
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    for key, value in event_data.model_dump().items():
        setattr(event, key, value)
    try:
        db.commit()
        db.refresh(event)
        return EventRead.model_validate(event)
    except Exception as e:
        db.rollback()
        print("Unexpected Error:", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {str(e)}"
        )


async def delete_event(event_id: int, db: Session) -> bool:
    """
    Deletes an event by its ID.

    Parameters:
        event_id (int): The unique identifier of the event.
        db (Session): Database session dependency.

    Returns:
        bool: True if deletion was successful, False if event not found.
    """
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        return False
    db.delete(event)
    db.commit()
    return True
