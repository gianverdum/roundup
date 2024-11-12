# src/models/round.py
from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.orm import relationship

from src.database import Base


class Round(Base):
    """
    Represents a round in an event, managing participant-table allocations for unique connections.

    Attributes:
        id (int): Primary key for the round.
        event_id (int): Foreign key to the associated event.
        round_number (int): Sequential round number in the event.
    """

    __tablename__ = "rounds"

    id: int = Column(Integer, primary_key=True, index=True)
    event_id: int = Column(Integer, ForeignKey("events.id"), nullable=False, index=True)
    round_number: int = Column(Integer, nullable=False)

    event = relationship("Event", back_populates="rounds")
    allocations = relationship("TableAllocation", back_populates="round", cascade="all, delete-orphan")
