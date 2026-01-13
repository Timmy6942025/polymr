"""Database configuration and session management."""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .models import Base

# Database URL from environment variable, default to SQLite
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./polymr.db")

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Get database session for dependency injection."""

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables."""

    Base.metadata.create_all(bind=engine)


def drop_db():
    """Drop all database tables."""

    Base.metadata.drop_all(bind=engine)
