# tests/test_allocation_service.py
import os
from typing import Generator

import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.database import Base, get_db
from src.main import app
from src.models.table import Table
from src.services.allocation_service import allocate_participants, calculate_rounds_needed
from tests.test_events import create_event
from tests.test_tables import create_table

# Load the database URL from the .env file
load_dotenv()
DATABASE_URL = os.getenv("POSTGRES_URL")

# Adjust the DATABASE_URL for compatibility
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

if DATABASE_URL:
    DATABASE_URL = DATABASE_URL.split("&supa=")[0]

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in the environment variables")

# Set up the database engine
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    connection = engine.connect()
    transaction = connection.begin()
    session = SessionLocal(bind=connection)
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    yield session

    session.close()
    if transaction.is_active:
        transaction.rollback()
    connection.close()


@pytest.fixture
def test_client(db_session: Session) -> Generator[TestClient, None, None]:
    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app) as client:
        yield client


def test_calculate_rounds_needed() -> None:
    total_participants = 16
    seats_per_table = 4
    table_count = 4
    rounds_needed = calculate_rounds_needed(total_participants, seats_per_table, table_count)
    assert rounds_needed > 0, "Rounds needed calculation failed, must be greater than zero."


def test_no_repeated_table_groups_across_rounds(test_client: TestClient) -> None:
    event_id = create_event(test_client)
    table_quantity = 4
    seats_per_table = 2
    create_table(test_client, event_id=event_id, quantity=table_quantity, seats=seats_per_table)

    response = test_client.get(f"/api/tables?event_id={event_id}")
    assert response.status_code == 200, f"Failed to fetch tables: {response.json()}"
    tables = [
        Table(
            id=table_data["id"], event_id=event_id, table_number=table_data["table_number"], seats=table_data["seats"]
        )
        for table_data in response.json()["items"]
    ]

    participants = list(range(1, table_quantity * seats_per_table + 1))
    required_rounds = calculate_rounds_needed(len(participants), seats_per_table, table_quantity)
    rounds = allocate_participants(participants, tables, max_rounds=required_rounds)

    seen_groups = set()
    for round_allocation in rounds.values():
        for table in tables:
            table_participants = tuple(sorted(round_allocation[table.id]))
            if table_participants:
                assert table_participants not in seen_groups, f"Repeated group found: {table_participants}"
                seen_groups.add(table_participants)


def test_allocate_participants_basic(test_client: TestClient) -> None:
    event_id = create_event(test_client)
    table_quantity = 2
    seats_per_table = 2
    create_table(test_client, event_id=event_id, quantity=table_quantity, seats=seats_per_table)

    response = test_client.get(f"/api/tables?event_id={event_id}")
    assert response.status_code == 200, f"Failed to fetch tables: {response.json()}"
    tables = [
        Table(
            id=table_data["id"], event_id=event_id, table_number=table_data["table_number"], seats=table_data["seats"]
        )
        for table_data in response.json()["items"]
    ]

    participants = list(range(1, table_quantity * seats_per_table + 1))
    required_rounds = calculate_rounds_needed(len(participants), seats_per_table, table_quantity)
    rounds = allocate_participants(participants, tables, max_rounds=required_rounds)

    print("\nAllocation results for manual verification:")
    print(rounds)

    for round_allocation in rounds.values():
        for table in tables:
            assigned_participants = round_allocation[table.id]
            assert len(assigned_participants) <= table.seats, "Exceeded seats per table"

    for round_allocation in rounds.values():
        all_assigned = sum(round_allocation.values(), [])
        assert len(all_assigned) == len(set(all_assigned)), "Repeated participants in a single round"
