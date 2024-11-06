# src/models/table.py
from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.orm import relationship

from src.database import Base


class Table(Base):
    """
    Represents a table at an event.

    Attributes:
        id (int): Primary key for the table record.
        event_id (int): Foreign key linking to the associated event.
        table_number (int): Number identifying the table within the event.
        seats (int): Number of seats available at the table.
    """

    __tablename__ = "tables"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"))
    table_number = Column(Integer, nullable=False)
    seats = Column(Integer, nullable=False)

    event = relationship("Event", back_populates="tables")

    def __repr__(self) -> str:
        return f"<Table id={self.id} event_id={self.event_id} table_number={self.table_number} seats={self.seats}>"
