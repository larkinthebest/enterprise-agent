"""SQLAlchemy engine & session factory.

Engine is lazily created to avoid connecting at import time during tests.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.core.config import settings

_engine = None
_SessionLocal = None


def get_engine():
    """Get or create the SQLAlchemy engine (lazy singleton)."""
    global _engine
    if _engine is None:
        _engine = create_engine(
            settings.database_url,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            echo=(settings.app_env == "dev"),
        )
    return _engine


# For backwards compat — modules that import `engine` directly
engine = property(lambda self: get_engine())


def get_session_factory():
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())
    return _SessionLocal


def get_db():
    """FastAPI dependency — yields a DB session per request."""
    factory = get_session_factory()
    db = factory()
    try:
        yield db
    finally:
        db.close()
