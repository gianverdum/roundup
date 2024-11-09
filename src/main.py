# src/main.py
import logging
import traceback
from typing import Callable

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import OperationalError, SQLAlchemyError

from src.database import Base, engine
from src.routers import events, participants, tables

load_dotenv()

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="RoundUp API",
    description="API for managing events, tables, and participants in the RoundUp business rounds.",
    version="1.0.0",
    contact={
        "name": "Giancarlo Verdum",
        "url": "https://github.com/gianverdum/roundup",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
)


logging.basicConfig(level=logging.DEBUG)


@app.middleware("http")
async def db_error_handler(request: Request, call_next: Callable[[Request], JSONResponse]) -> JSONResponse:
    """Middleware for handling database errors with detailed responses."""
    try:
        response = await call_next(request)
        return response
    except OperationalError as op_err:
        logging.error(f"Database operational error: {op_err}")
        return JSONResponse(status_code=500, content={"detail": f"Database error: {str(op_err.orig)}"})
    except SQLAlchemyError as sql_err:
        logging.error(f"SQLAlchemy error: {sql_err}")
        return JSONResponse(status_code=500, content={"detail": f"Unexpected database error: {str(sql_err)}"})
    except Exception as e:
        error_trace = traceback.format_exc()  # Capture the traceback
        logging.error(f"Unexpected error: {e}\n{error_trace}")  # Log full traceback
        return JSONResponse(
            status_code=500,
            content={
                "detail": "An unexpected error occurred",
                "error": str(e),
                "traceback": error_trace,  # Return traceback in response for debugging
            },
        )


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this for security in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Root endpoint
@app.get("/", summary="Root endpoint", response_description="Welcome message")
def read_root() -> dict[str, str]:
    """
    Root endpoint providing a welcome message.

    Returns:
        dict[str, str]: A JSON welcome message.
    """
    return {"message": "Welcome to the RoundUp API!"}


app.include_router(events.router, tags=["Events"])
app.include_router(tables.router, tags=["Tables"])
app.include_router(participants.router, tags=["Participants"])
