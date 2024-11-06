# src/models/event.py
from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from src.database import Base


class Event(Base):
    """
    Represents an event with various details.

    Attributes:
        id (int): Primary key for the event record.
        name (str): Name of the event.
        date (datetime): Date and time of the event.
        location (str): Location of the event.
        address (str): Address for the event.
        participant_limit (int): Max number of participants allowed.
        max_seats_per_table (int): Max seats allowed per table for the event.
    """

    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    date = Column(DateTime, default=datetime.now)
    location = Column(String)
    address = Column(String)
    participant_limit = Column(Integer)
    max_seats_per_table = Column(Integer, nullable=False)

    tables = relationship("Table", back_populates="event")

    def __repr__(self) -> str:
        return (
            f"<Event(name={self.name!r}, "
            f"date={self.date}, "
            f"location={self.location!r}, "
            f"address={self.address!r})>"
        )
