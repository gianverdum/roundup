# src/models/table_allocation.py
from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.orm import relationship

from src.database import Base


class TableAllocation(Base):
    """
    Represents the allocation of a participant to a specific table during a specific round.

    Attributes:
        id (int): Primary key for the table allocation record.
        round_id (int): Foreign key linking to the associated round.
        table_id (int): Foreign key linking to the specific table.
        participant_id (int): Foreign key linking to the allocated participant.
        round (relationship): Reference to the associated Round.
        table (relationship): Reference to the associated Table.
        participant (relationship): Reference to the allocated Participant.
    """

    __tablename__ = "table_allocations"

    id: int = Column(Integer, primary_key=True, index=True)
    round_id: int = Column(Integer, ForeignKey("rounds.id"), nullable=False, index=True)
    table_id: int = Column(Integer, ForeignKey("tables.id"), nullable=False, index=True)
    participant_id: int = Column(Integer, ForeignKey("participants.id"), nullable=False, index=True)

    round = relationship("Round", back_populates="allocations")
    table = relationship("Table")
    participant = relationship("Participant")

    def __repr__(self) -> str:
        return (
            f"<TableAllocation(id={self.id}, round_id={self.round_id}, "
            f"table_id={self.table_id}, participant_id={self.participant_id})>"
        )
