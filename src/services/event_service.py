# src/services/event_service.py
from datetime import datetime
from math import ceil
from typing import Any, Dict, Optional

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
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


async def get_all_events(db: Session, limit: int, offset: int) -> Dict[str, Any]:
    """
    Retrieves a paginated list of all events with the total number of records and pages.

    Parameters:
        db (Session): Database session dependency.
        limit (int): Maximum number of events to return.
        offset (int): Starting index for pagination.

    Returns:
        Dict[str, Any]: A dictionary compatible with EventPaginatedResponse.
    """
    try:
        total_records = db.query(Event).count()
        events = db.query(Event).offset(offset).limit(limit).all()

        return {
            "total_records": total_records,
            "total_pages": ceil(total_records / limit),
            "events": events,
        }

    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=500, detail="Database query failed. Please check the database connection or query logic."
        ) from e


async def filter_events(
    name: Optional[str],
    date: Optional[datetime],
    location: Optional[str],
    participant_limit: Optional[int],
    max_seats_per_table: Optional[int],
    db: Session,
    limit: int,
    offset: int,
) -> Dict[str, Any]:
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
        Dict[str, Any]: A dictionary containing the filtered list of events, total records, and total pages.

    Raises:
        HTTPException: If database connection fails or no events match the filter criteria.
    """
    try:
        query = db.query(Event)

        if name:
            query = query.filter(Event.name.ilike(f"%{name}%"))
        if date:
            query = query.filter(Event.date == date)
        if location:
            query = query.filter(Event.location.ilike(f"%{location}%"))
        if participant_limit:
            query = query.filter(Event.participant_limit == participant_limit)
        if max_seats_per_table:
            query = query.filter(Event.max_seats_per_table == max_seats_per_table)

        total_records = query.count()
        events = query.offset(offset).limit(limit).all()

        if not events:
            raise HTTPException(status_code=404, detail="No events found matching the filter criteria.")

        return {
            "total_records": total_records,
            "total_pages": ceil(total_records / limit),
            "events": events,
        }

    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=500, detail="Database connection failed or there was an error processing the request."
        ) from e


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
