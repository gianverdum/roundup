from typing import List

from sqlalchemy.orm import Session

from src.models.event import Event
from src.models.table import Table
from src.schemas.table import TableCreate, TableResponse


def create_tables(db: Session, table_data: TableCreate) -> List[TableResponse]:
    """
    Creates multiple tables in the database.

    Args:
        db (Session): Database session.
        table_data (TableCreate): Data for the tables to be created.

    Returns:
        List[TableResponse]: List of created TableResponse objects.

    Raises:
        ValueError: If the associated event is not found or if the seats exceed the event's limit.
        TypeError: If an invalid data type is passed.
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
