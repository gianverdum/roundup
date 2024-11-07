# src/models/participant.py
from sqlalchemy import Column, Integer, String, Text

from src.database import Base


class Participant(Base):
    __tablename__ = "participants"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(255), nullable=False)
    company_name = Column(String(255), nullable=False)
    whatsapp = Column(String(20), nullable=False)
    email = Column(String(255), nullable=False)
    custom_data = Column(Text, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<Participant(id={self.id}), "
            f"full_name={self.full_name!r}, "
            f"company_name={self.company_name!r}, "
            f"whatsapp={self.whatsapp!r}, "
            f"email={self.email!r}, "
            f"custom_data={self.custom_data!r})>"
        )
