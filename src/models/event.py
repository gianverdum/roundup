# src/models/event.py
from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String

from src.database import Base


class Event(Base):
    """
    Represents an event with attributes such as name, date, location, participant limit, and address.

    Attributes:
        id (int): Primary key for the event record.
        name (str): Name of the event.
        date (datetime): Date and time of the event.
        location (str): Location where the event will take place.
        participant_limit (int): Maximum number of participants allowed.
        address (str): Address of the event.
    """

    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    date = Column(DateTime, default=datetime.now)
    location = Column(String)
    address = Column(String)
    participant_limit = Column(Integer)

    def __repr__(self) -> str:
        return f"<Event(name={self.name}, date={self.date}, location={self.location})"
