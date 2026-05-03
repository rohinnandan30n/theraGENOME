"""Database connection and session management."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from typing import Generator
import os

# Use SQLite for demo/dev, PostgreSQL in production
# DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/pathogen_db")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./pathogen_resistance.db")

# Create engine based on database type
if "sqlite" in DATABASE_URL:
    # SQLite connection for development
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
else:
    # PostgreSQL connection for production
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        echo=False,
    )

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency injection for database session.
    
    Yields:
        SQLAlchemy Session for database operations
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables."""
    from src.db.models import Base
    Base.metadata.create_all(bind=engine)
