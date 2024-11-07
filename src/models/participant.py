# src/models/participant.py
from sqlalchemy import Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from src.database import Base


class Participant(Base):
    """
    Represents the Participant with various details.

    Attributes:
        full_name (str): Full name of the participant.
        company_name (str): Company the participant is representing.
        whatsapp (str): Participant's WhatsApp number.
        email (str): Participant's email address.
        custom_data (dict, optional): Additional dynamic fields specific to the event.
        event_id (int): ID of the associated event.
    """

    __tablename__ = "participants"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(255), nullable=False)
    company_name = Column(String(255), nullable=False)
    whatsapp = Column(String(20), nullable=False)
    email = Column(String(255), nullable=False)
    custom_data = Column(Text, nullable=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)

    event = relationship("Event", back_populates="participants")

    def __repr__(self) -> str:
        return (
            f"<Participant(id={self.id}), "
            f"full_name={self.full_name!r}, "
            f"company_name={self.company_name!r}, "
            f"whatsapp={self.whatsapp!r}, "
            f"email={self.email!r}, "
            f"custom_data={self.custom_data!r})>"
        )
