# src/models/round.py
from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.orm import relationship

from src.database import Base


class Round(Base):
    """
    Represents a round within an event, managing participant-table allocations
    to facilitate unique interactions across different rounds.

    Attributes:
        id (int): Primary key for the round record.
        event_id (int): Foreign key linking to the associated event.
        round_number (int): Sequential number of the round within the event.
        event (relationship): Reference to the associated Event.
        allocations (relationship): List of table allocations for this round.
    """

    __tablename__ = "rounds"

    id: int = Column(Integer, primary_key=True, index=True)
    event_id: int = Column(Integer, ForeignKey("events.id"), nullable=False, index=True)
    round_number: int = Column(Integer, nullable=False)

    event = relationship("Event", back_populates="rounds")
    allocations = relationship("TableAllocation", back_populates="round", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Round(id={self.id}, event_id={self.event_id}, round_number={self.round_number})>"
