# src/database.py
import os
from typing import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

load_dotenv()

# Retrieve and modify the PostgreSQL connection URL from the environment
DATABASE_URL = os.getenv("POSTGRES_URL")

# Replace the 'postgres://' prefix with 'postgresql://' if necessary
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Remove unwanted string from DATABASE_URL
if DATABASE_URL:
    DATABASE_URL = DATABASE_URL.split("&supa=")[0]

# Raise an error if the DATABASE_URL is missing after loading
if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in the environment variables")


engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Dependency that provides a SQLAlchemy database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
