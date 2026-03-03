"""
Database configuration and Appointment model
For Voice Medical Agent backend
"""

import datetime
from typing import Generator
from sqlalchemy.orm import Session

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Integer,
    String,
    create_engine
)
from sqlalchemy.orm import declarative_base, sessionmaker, Session


# ============================================================
# DATABASE CONFIGURATION
# ============================================================

# SQLite database file (local development)
DATABASE_URL = "sqlite:///./appointments.db"

# Create SQLAlchemy engine
# check_same_thread=False is required for SQLite when using FastAPI
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# Session factory
# autocommit=False → You manually commit changes
# autoflush=False → Avoid auto-flushing before commit
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base class for all models
Base = declarative_base()


# ============================================================
# APPOINTMENT MODEL
# ============================================================

class Appointment(Base):
    """
    Database model for storing patient appointments
    """

    __tablename__ = "appointments"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Patient full name
    patient_name = Column(String, index=True, nullable=False)

    # Reason for appointment (e.g., fever, consultation)
    reason = Column(String, index=True, nullable=False)

    # Appointment start date & time
    start_time = Column(DateTime, index=True, nullable=False)

    # If appointment is canceled
    canceled = Column(Boolean, default=False)

    # When appointment record was created
    created_at = Column(
        DateTime,
        default=datetime.datetime.utcnow
    )


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def init_db() -> None:
    """
    Create all tables in the database.
    Call this once at application startup.
    """
    Base.metadata.create_all(bind=engine)


# ============================================================
# DATABASE DEPENDENCY (FastAPI)
# ============================================================

def get_db() -> Generator[Session, None, None]:
    """
    Dependency for getting a database session.
    Automatically closes session after request completes.
    """
    db:Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Uncomment this if you want to create tables manually
# init_db()
