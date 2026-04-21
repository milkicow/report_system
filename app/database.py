"""SQLAlchemy engine, session factory, declarative base, and DB dependency."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

SQLALCHEMY_DATABASE_URL = "sqlite:///./reporting.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Declarative base class for all SQLAlchemy ORM models."""


def get_db():
    """Yield a database session and ensure it is closed when the request finishes."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
