# src/services/event_service.py
from datetime import datetime
from typing import List, Optional

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


async def get_all_events(db: Session, limit: int, offset: int) -> List[EventRead]:
    """
    Retrieves a paginated list of all events.

    Parameters:
        db (Session): Database session dependency.
        limit (int): Maximum number of events to return.
        offset (int): Starting index for pagination.

    Returns:
        List[EventRead]: A paginated list of all event records.
    """
    return db.query(Event).offset(offset).limit(limit).all()


async def filter_events(
    name: Optional[str],
    date: Optional[datetime],
    location: Optional[str],
    participant_limit: Optional[int],
    max_seats_per_table: Optional[int],
    db: Session,
    limit: int,
    offset: int,
) -> List[EventRead]:
    """
    Filters and paginates events based on optional parameters.

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
        List[EventRead]: A paginated list of events matching the filters.
    """
    query = db.query(Event)

    if name:
        query = query.filter(Event.name.ilike(f"%{name}"))
    if date:
        query = query.filter(Event.date == date)
    if location:
        query = query.filter(Event.location.ilike(f"%{location}"))
    if participant_limit:
        query = query.filter(Event.participant_limit == participant_limit)
    if max_seats_per_table:
        query = query.filter(Event.max_seats_per_table == max_seats_per_table)

    return query.offset(offset).limit(limit).all()


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
