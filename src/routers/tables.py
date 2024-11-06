# src/routers/tables.py
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.database import get_db
from src.schemas.table import TableCreate, TableResponse
from src.services.table_service import create_tables

router = APIRouter()


@router.post(
    "/api/tables/",
    response_model=List[TableResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Register multiple tables",
    description="Endpoint to register multiple tables for a specific event. "
    "Each table will be associated with an event and have a configurable number of seats.",
    responses={
        201: {"description": "Tables successfully created"},
        400: {"description": "Invalid data or constraint violation"},
    },
)
async def register_tables(table_data: TableCreate, db: Session = Depends(get_db)) -> List[TableResponse]:
    """
    API endpoint to register multiple tables for an event.

    Args:
        table_data (TableCreate): Data for the new tables.
        db (Session): Database session dependency.

    Returns:
        List[TableResponse]: List of the registered tables' data including their IDs and table numbers.

    Raises:
        HTTPException: If the event is not found or if the seats exceed the limit.
    """
    try:
        db_tables = create_tables(db=db, table_data=table_data)
        return db_tables
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
