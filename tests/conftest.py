# tests/conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from src.main import app
from src.database import Base, get_db

# In-memory database configuration for testing
DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Fixture to set up the database and create tables before each test
@pytest.fixture(scope="function")
def db_session():
    """Creates tables before each test and drops them afterward to ensure isolation."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


# Fixture for TestClient, injecting db_session into the app
@pytest.fixture(scope="function")
def test_client(db_session):
    """Overrides the app's database dependency to use the in-memory test database."""
    def override_get_db():
        try:
            yield db_session
        finally:
            db_session.close()

    # Override the app's database dependency with the test database session
    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
