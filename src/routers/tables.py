# src/routers/tables.py
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from src.database import get_db
from src.schemas.table import TableCreate, TablePaginatedResponse, TableResponse, TableUpdate
from src.services.table_service import (
    create_tables,
    delete_table,
    filter_tables,
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
    "/api/tables/",
    status_code=status.HTTP_200_OK,
    response_model=TablePaginatedResponse,
    summary="Get all tables with pagination",
    responses={
        200: {
            "description": "List of paginated tables returned successfully",
            "content": {
                "application/json": {
                    "example": {
                        "items": [
                            {
                                "id": 1,
                                "event_id": 1,
                                "table_number": 1,
                                "seats": 8,
                            },
                            {
                                "id": 2,
                                "event_id": 1,
                                "table_number": 2,
                                "seats": 8,
                            },
                        ],
                        "total_items": 2,
                        "total_pages": 1,
                        "current_page": 1,
                        "page_size": 10,
                    }
                }
            },
        },
        500: {
            "description": "Database connection failed or error in request processing.",
        },
    },
)
async def read_tables_route(
    db: Session = Depends(get_db),
    limit: int = Query(10, ge=1, description="Limit the number of results", examples=5),
    offset: int = Query(0, ge=0, description="The starting index of results", examples=0),
) -> TablePaginatedResponse:
    """
    Retrieves a paginated list of all tables with total records and pages.

    Parameters:
        db (Session): Database session dependency.
        limit (int): Maximum number of tables to return.
        offset (int): Starting index for pagination.

    Returns:
        TablePaginatedResponse: A paginated list of all tables.
    """
    filter_results = await get_all_tables(db, limit=limit, offset=offset)

    return TablePaginatedResponse(
        items=[TableResponse.model_validate(table.__dict__) for table in filter_results["tables"]],
        total_items=filter_results["total_records"],
        total_pages=filter_results["total_pages"],
        current_page=(offset // limit) + 1,
        page_size=limit,
    )


@router.get(
    "/api/tables/filter",
    status_code=status.HTTP_200_OK,
    response_model=TablePaginatedResponse,
    summary="Filter tables with pagination",
    responses={
        200: {
            "description": "Filtered and paginated list of tables returned successfully",
            "content": {
                "application/json": {
                    "example": {
                        "items": [
                            {
                                "id": 1,
                                "event_id": 1,
                                "table_number": 1,
                                "seats": 8,
                            },
                        ],
                        "total_items": 1,
                        "total_pages": 1,
                        "current_page": 1,
                        "page_size": 10,
                    }
                }
            },
        },
        404: {
            "description": "No tables found matching the filter criteria.",
        },
        500: {
            "description": "Database connection failed or error in request processing.",
        },
    },
)
async def filter_tables_route(
    event_id: Optional[int] = Query(None, description="Filter by event ID", examples=1),
    table_number: Optional[int] = Query(None, description="Filter by table number", examples=1),
    db: Session = Depends(get_db),
    limit: int = Query(10, ge=1, description="Limit the number of results", examples=5),
    offset: int = Query(0, ge=0, description="The starting index of results", examples=0),
) -> TablePaginatedResponse:
    """
    Retrieves a paginated list of tables filtered by the provided parameters.

    Parameters:
        event_id (int, optional): Event ID to filter by.
        table_number (int, optional): Table number to filter by.
        db (Session): Database session dependency.
        limit (int): Maximum number of tables to return.
        offset (int): Starting index for pagination.

    Returns:
        TablePaginatedResponse: A paginated list of tables matching the filters.

    Raises:
        HTTPException: If no tables are found or a database error occurs.
    """
    filter_results = await filter_tables(event_id, table_number, db, limit, offset)

    return TablePaginatedResponse(
        items=[TableResponse.model_validate(table.__dict__) for table in filter_results["tables"]],
        total_items=filter_results["total_records"],
        total_pages=filter_results["total_pages"],
        current_page=(offset // limit) + 1,
        page_size=limit,
    )


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
async def update_table_route(table_id: int, table_data: TableUpdate, db: Session = Depends(get_db)) -> TableResponse:
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
    return TableResponse.model_validate(updated_table)


@router.delete(
    "/api/tables/{table_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete table", response_class=Response
)
async def delete_table_route(table_id: int, db: Session = Depends(get_db)) -> None:
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
