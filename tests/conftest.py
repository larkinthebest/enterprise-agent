"""Shared pytest fixtures."""

import os
import secrets
import pytest

# Set test env vars BEFORE importing app modules
os.environ.update({
    "APP_ENV": "test",
    "POSTGRES_HOST": "localhost",
    "POSTGRES_PORT": "5432",
    "POSTGRES_DB": "agent_test",
    "POSTGRES_USER": "test",
    "POSTGRES_PASSWORD": "test",
    "REDIS_HOST": "localhost",
    "REDIS_PORT": "6379",
    "QDRANT_HOST": "localhost",
    "QDRANT_PORT": "6333",
    "LANGFUSE_HOST": "http://localhost:3000",
    "LANGFUSE_PUBLIC_KEY": "test",
    "LANGFUSE_SECRET_KEY": "test",
    "OPENAI_API_KEY": "sk-test",
})

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from contextlib import asynccontextmanager

from app.db.base import Base


# ── In-memory SQLite for tests ───────────────────────────────────────────
_test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False,
)
Base.metadata.create_all(bind=_test_engine)

_TestSession = sessionmaker(autocommit=False, autoflush=False, bind=_test_engine)


@pytest.fixture()
def db_session():
    session = _TestSession()
    yield session
    session.rollback()
    session.close()


@pytest.fixture()
def client(db_session):
    """FastAPI test client with DB dependency override and no-op lifespan."""
    import app.db.session as session_module

    # Patch get_engine to return our SQLite engine
    original_engine = session_module._engine
    session_module._engine = _test_engine

    from app.db.session import get_db

    # Import app AFTER patching engine
    from app.main import app

    # Override DB dependency
    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db

    with TestClient(app, raise_server_exceptions=False) as c:
        yield c

    app.dependency_overrides.clear()
    # Restore original engine (don't let dispose() kill our StaticPool)
    session_module._engine = original_engine


@pytest.fixture()
def admin_user(db_session):
    """Create an admin user and return (user, api_key)."""
    from app.db.models.user import User, Role

    api_key = secrets.token_hex(32)
    user = User(username=f"testadmin_{secrets.token_hex(4)}", api_key=api_key, role=Role.ADMIN, full_name="Test Admin")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user, api_key


@pytest.fixture()
def operator_user(db_session):
    """Create an operator user and return (user, api_key)."""
    from app.db.models.user import User, Role

    api_key = secrets.token_hex(32)
    user = User(username=f"testoperator_{secrets.token_hex(4)}", api_key=api_key, role=Role.OPERATOR, full_name="Test Operator")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user, api_key
