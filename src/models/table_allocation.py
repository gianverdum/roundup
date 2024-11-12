# src/models/table_allocation.py
from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.orm import relationship

from src.database import Base


class TableAllocation(Base):
    """
    Represents the allocation of a participant to a specific table in a specific round.

    Attributes:
        id (int): Primary key for the table allocation record.
        round_id (int): Foreign key to the associated round.
        table_id (int): Foreign key to the specific table.
        participant_id (int): Foreign key to the allocated participant.
    """

    __tablename__ = "table_allocations"

    id: int = Column(Integer, primary_key=True, index=True)
    round_id: int = Column(Integer, ForeignKey("rounds.id"), nullable=False, index=True)
    table_id: int = Column(Integer, ForeignKey("tables.id"), nullable=False, index=True)
    participant_id: int = Column(Integer, ForeignKey("participants.id"), nullable=False, index=True)

    round = relationship("Round", back_populates="allocations")
    table = relationship("Table")
    participant = relationship("Participant")
