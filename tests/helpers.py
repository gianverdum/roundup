# tests/helpers.py
import random
from datetime import datetime, timedelta
from typing import Any, Optional

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.models.participant import Participant
from src.schemas.event import EventCreate
from src.schemas.participant import ParticipantCreate
from src.schemas.table import TableCreate


# 1. Generate unique event data
def generate_unique_event() -> EventCreate:
    """Generate a unique event with random data."""
    date = datetime.now() + timedelta(days=random.randint(1, 30))
    return EventCreate(
        name=f"Event {random.randint(1, 10000)}",
        date=date,
        location=f"Location {random.randint(1, 100)}",
        address=f"{random.randint(1, 1000)} - Sample Address, São Paulo - SP, 01310-{random.randint(100, 999)}",
        participant_limit=random.randint(10, 100),
        max_seats_per_table=random.randint(2, 8),
        tables_count=random.randint(1, 20),
    )


# 2. Generate unique participant data
def generate_unique_participant(event_id: int) -> ParticipantCreate:
    """Generate a unique participant with random data."""
    custom_data = {
        "membership_level": random.choice(["Silver", "Gold", "Platinum"]),
        "preferences": random.choice(["Vegetarian", "Non-Vegetarian", "Vegan"]),
        "registration_time": random.randint(1000000000, 9999999999),
    }
    full_name = f"Participant{random.randint(1, 10000)} {random.choice(['Smith', 'Johnson', 'Williams'])}"
    whatsapp = f"+5511{random.randint(100000000, 999999999)}"
    email = f"participant{random.randint(1, 10000)}@example.com"
    return ParticipantCreate(
        full_name=full_name,
        company_name=f"Company {random.randint(1, 100)}",
        whatsapp=whatsapp,
        email=email,
        event_id=event_id,
        custom_data=custom_data,
    )


# 3. Generate table data
def generate_data_table(event_id: int, quantity: Optional[int] = None, seats: Optional[int] = None) -> TableCreate:
    """Generate a table creation schema."""
    return TableCreate(
        event_id=event_id,
        quantity=quantity if quantity is not None else random.randint(2, 12),
        seats=seats if seats is not None else random.randint(2, 10),
    )


# 4. Create an event using the client
def create_event_with_isoformat(test_client: TestClient) -> dict[str, Any]:
    """Helper function to create an event and return its JSON data."""
    event_data = generate_unique_event()
    event_data.max_seats_per_table = 10
    event_data_dict = event_data.model_dump()
    for key, value in event_data_dict.items():
        if isinstance(value, datetime):
            event_data_dict[key] = value.isoformat()

    response = test_client.post("/api/events/", json=event_data_dict)
    assert response.status_code == 201
    return response.json()


# 5. Create a table using the client
def create_table(
    test_client: TestClient, event_id: int, quantity: Optional[int] = None, seats: Optional[int] = None
) -> int:
    """Helper function to create tables and return the table ID."""
    table_data = generate_data_table(event_id=event_id, quantity=quantity, seats=seats)
    response = test_client.post("/api/tables/", json=table_data.model_dump())
    if response.status_code != 201:
        print("Error creating table:", response.json())
    assert response.status_code == 201
    return response.json()[0]["id"]


# 6. Create a participant using the client
def create_participant(test_client: TestClient, event_id: int) -> int:
    """Helper function to create a participant and return their ID."""
    participant_data = generate_unique_participant(event_id)
    response = test_client.post("/api/participants/", json=participant_data.model_dump())
    assert response.status_code == 201
    return response.json()["id"]


def add_participant(
    db: Session,
    event_id: int,
    full_name: str = "John Doe",
    company_name: str = "Test Corp",
    whatsapp: str = "12345678901",
    email: str = "johndoe@test.com",
    is_present: bool = False,
) -> Participant:
    """
    Add a participant to the database.

    Args:
        db (Session): The database session.
        event_id (int): ID of the event the participant is attending.
        full_name (str): Full name of the participant.
        company_name (str): Company name.
        whatsapp (str): WhatsApp contact.
        email (str): Email address.
        is_present (bool): Check-in status.

    Returns:
        Participant: The added participant instance.
    """
    participant = Participant(
        full_name=full_name,
        company_name=company_name,
        whatsapp=whatsapp,
        email=email,
        event_id=event_id,
        is_present=is_present,
    )
    db.add(participant)
    db.commit()
    db.refresh(participant)
    return participant


def check_in_participant(db: Session, participant_id: int) -> Participant:
    """
    Mark a participant as checked-in.

    Args:
        db (Session): The database session.
        participant_id (int): ID of the participant to check-in.

    Returns:
        Participant: The checked-in participant instance.
    """
    participant = db.query(Participant).filter(Participant.id == participant_id).first()
    if participant:
        participant.is_present = True
        db.commit()
        db.refresh(participant)
    return participant
