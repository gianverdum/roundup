# src/services/table_service.py
from math import ceil
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from src.models.event import Event
from src.models.table import Table
from src.schemas.table import TableCreate, TableResponse, TableUpdate


def create_tables(db: Session, table_data: TableCreate) -> List[TableResponse]:
    """
    Creates multiple tables for an event in the database.

    Args:
        db (Session): Database session.
        table_data (TableCreate): Data for tables, including event ID, quantity, and seats.

    Returns:
        List[TableResponse]: List of created tables.

    Raises:
        ValueError: If the event is not found or seats exceed the event's limit.
        TypeError: If non-integer values are provided for seats or quantity.
    """
    if not isinstance(table_data.seats, int) or not isinstance(table_data.quantity, int):
        raise TypeError("Seats and quantity must be integers.")

    event = db.query(Event).filter(Event.id == table_data.event_id).first()
    if not event:
        raise ValueError("Event not found")

    max_seats = event.max_seats_per_table
    if table_data.seats > max_seats:
        raise ValueError(f"Number of seats exceeds the maximum allowed per table ({max_seats})")

    created_tables = []
    try:
        for i in range(1, table_data.quantity + 1):
            db_table = Table(event_id=table_data.event_id, table_number=i, seats=table_data.seats)
            db.add(db_table)
            created_tables.append(db_table)

        db.commit()  # Commit once after all tables are added
        for table in created_tables:
            db.refresh(table)  # Refresh each table instance after commit

    except Exception:
        db.rollback()  # Rollback in case of error
        raise

    # Convert each table to a TableResponse and return the list
    return [
        TableResponse(id=table.id, event_id=table.event_id, seats=table.seats, table_number=table.table_number)
        for table in created_tables
    ]


async def get_table_by_id(table_id: int, db: Session) -> TableResponse:
    """
    Fetches a table by its unique ID.

    Args:
        table_id (int): ID of the table.
        db (Session): Database session dependency.

    Returns:
        TableResponse: The requested table, if found.
    """
    return db.query(Table).filter(Table.id == table_id).first()


async def get_all_tables(db: Session, limit: int, offset: int) -> Dict[str, Any]:
    """
    Retrieves a paginated list of all tables with the total number of records and pages.

    Parameters:
        db (Session): Database session dependency.
        limit (int): Maximum number of tables to return.
        offset (int): Starting index for pagination.

    Returns:
        Dict[str, Any]: A dictionary compatible with TablePaginatedResponse.
    """
    try:
        total_records = db.query(Table).count()
        tables = db.query(Table).offset(offset).limit(limit).all()

        return {
            "total_records": total_records,
            "total_pages": ceil(total_records / limit),
            "tables": tables,
        }

    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=500, detail="Database query failed. Please check the database connection or query logic."
        ) from e


async def filter_tables(
    event_id: Optional[int],
    table_number: Optional[int],
    db: Session,
    limit: int,
    offset: int,
) -> Dict[str, Any]:
    """
    Filters and paginates tables based on optional parameters.

    Parameters:
        event_id (int, optional): Event ID to filter by.
        table_number (int, optional): Table number to filter by.
        db (Session): Database session dependency.
        limit (int): Maximum number of tables to return.
        offset (int): Starting index for pagination.

    Returns:
        Dict[str, Any]: A dictionary containing the filtered list of tables, total records, and total pages.

    Raises:
        HTTPException: If database connection fails or no tables match the filter criteria.
    """
    try:
        query = db.query(Table)

        if event_id:
            query = query.filter(Table.event_id == event_id)
        if table_number:
            query = query.filter(Table.table_number == table_number)

        total_records = query.count()
        tables = query.offset(offset).limit(limit).all()

        if not tables:
            raise HTTPException(status_code=404, detail="No tables found matching the filter criteria.")

        return {
            "total_records": total_records,
            "total_pages": ceil(total_records / limit),
            "tables": tables,
        }

    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=500, detail="Database connection failed or there was an error processing the request."
        ) from e


async def update_table(table_id: int, table_data: TableUpdate, db: Session) -> Optional[dict[str, Any]]:
    """
    Updates table details.

    Args:
        table_id (int): ID of the table to update.
        table_data (TableCreate): Data for updating the table.
        db (Session): Database session dependency.

    Returns:
        TableResponse: Updated table details if successful.

    Raises:
        HTTPException: For any unexpected error during the update process.
    """
    table = db.query(Table).filter(Table.id == table_id).first()
    if not table:
        return None

    for key, value in table_data.model_dump().items():
        setattr(table, key, value)

    try:
        db.commit()
        db.refresh(table)

        return {"id": table.id, "event_id": table.event_id, "table_number": table.table_number, "seats": table.seats}
    except Exception as e:
        db.rollback()
        print("Unexpected Error:", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error ocurred: {str(e)}"
        )


async def delete_table(table_id: int, db: Session) -> bool:
    """
    Deletes a table by its ID.

    Args:
        table_id (int): Unique identifier for the table.
        db (Session): Database session.

    Returns:
        bool: True if deletion was successful, False if table was not found.
    """
    table = db.query(Table).filter(Table.id == table_id).first()
    if not table:
        return False
    db.delete(table)
    db.commit()
    return True
