# src/main.py
from dotenv import load_dotenv
from fastapi import FastAPI

from src.database import Base, engine
from src.routers import events, participants, tables

load_dotenv()


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


Base.metadata.create_all(bind=engine)


app.include_router(events.router, tags=["Events"])
app.include_router(tables.router, tags=["Tables"])
app.include_router(participants.router, tags=["Participants"])
