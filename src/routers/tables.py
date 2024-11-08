# src/routers/tables.py
from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.database import get_db
from src.schemas.table import TableCreate, TableResponse
from src.services.table_service import (
    create_tables,
    delete_table,
    get_all_tables,
    get_table_by_id,
    update_table,
)

router = APIRouter()


@router.post(
    "/api/tables/",
    response_model=List[TableResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Register multiple tables",
    description="Endpoint to register multiple tables for a specific event. "
    "Each table will be associated with an event and have a configurable number of seats.",
    responses={
        201: {
            "description": "Table created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "event_id": 1,
                        "table_number": 1,
                        "seats": 1,
                    }
                }
            },
        },
        400: {"description": "Invalid data or constraint violation"},
        404: {"description": "Table not found"},
    },
)
async def register_tables(table_data: TableCreate, db: Session = Depends(get_db)) -> List[TableResponse]:
    """
    Registers multiple tables for a specified event.

    Args:
        table_data (TableCreate): Data for creating tables, including event ID and seat count.
        db (Session): Database session dependency.

    Returns:
        List[TableResponse]: List of registered tables with details like ID, event ID, and seat count.

    Raises:
        HTTPException: If data is invalid or a constraint is violated,
        such as event not found or seat count exceeds limit.
    """
    try:
        db_tables = create_tables(db=db, table_data=table_data)
        return db_tables
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/api/tables/{table_id}",
    status_code=status.HTTP_200_OK,
    response_model=TableResponse,
    summary="Get table by ID",
    responses={
        200: {
            "description": "Table returned successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "event_id": 1,
                        "table_number": 1,
                        "seats": 1,
                    }
                }
            },
        },
        400: {"description": "Invalid data or constraint violation"},
        404: {"description": "Table not found"},
    },
)
async def read_table_route(table_id: int, db: Session = Depends(get_db)) -> TableResponse:
    """
    Retrieves a table by its ID.

    Args:
        table_id (int): Unique identifier for the table.
        db (Session): Database session dependency.

    Returns:
        TableResponse: Details of the retrieved table.

    Raises:
        HTTPException: If the table with the given ID is not found (404).
    """
    table = await get_table_by_id(table_id, db)
    if not table:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Table not found")
    return table


@router.get(
    "/api/tables/",
    status_code=status.HTTP_200_OK,
    response_model=List[TableResponse],
    summary="Get all tables",
    responses={
        200: {
            "description": "Table's list returned successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "event_id": 1,
                        "table_number": 1,
                        "seats": 1,
                    }
                }
            },
        },
        400: {"description": "Invalid data or constraint violation"},
    },
)
async def read_tables_route(db: Session = Depends(get_db)) -> List[TableResponse]:
    """
    Retrieves all tables in the database.

    Args:
        db (Session): Database session dependency.

    Returns:
        List[TableResponse]: List of all tables.
    """
    return await get_all_tables(db)


@router.put(
    "/api/tables/{table_id}",
    status_code=status.HTTP_200_OK,
    response_model=TableResponse,
    summary="Update table",
    responses={
        200: {
            "description": "Table updated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "event_id": 1,
                        "table_number": 1,
                        "seats": 1,
                    }
                }
            },
        },
        400: {"description": "Invalid data or constraint violation"},
        404: {"description": "Table not found"},
    },
)
async def update_table_route(table_id: int, table_data: TableCreate, db: Session = Depends(get_db)) -> TableResponse:
    """
    Updates a table's details based on table ID.

    Args:
        table_id (int): Unique identifier for the table.
        table_data (TableCreate): New data for the table.
        db (Session): Database session dependency.

    Returns:
        TableResponse: Updated table details.

    Raises:
        HTTPException: If the table is not found (404) or if any unexpected error occurs during update.
    """
    updated_table = await update_table(table_id, table_data, db)
    if not updated_table:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Table not found")
    return updated_table


@router.delete(
    "/api/tables/{table_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete table",
    responses={
        204: {"description": "Table deleted successfully"},
        400: {"description": "Bad Request"},
        404: {"description": "Table not found"},
    },
)
async def delete_table_route(table_id: int, db: Session = Depends(get_db)) -> Dict[str, str]:
    """
    Deletes a table by its ID.

    Args:
        table_id (int): Unique identifier for the table.
        db (Session): Database session dependency.

    Returns:
        Dict[str, str]: Message confirming deletion.

    Raises:
        HTTPException: If the table with the given ID is not found (404).
    """
    success = await delete_table(table_id, db)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Table not found")
    return {"detail": "Table deleted successfully"}
