"""Declarative base + common mixins + cross-dialect type helpers."""

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Boolean, String, TypeDecorator, JSON
from sqlalchemy.orm import DeclarativeBase

import uuid


class Base(DeclarativeBase):
    """Declarative base class for all ORM models."""

    pass


class TimestampMixin:
    """Adds created_at / updated_at columns."""

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class SoftDeleteMixin:
    """Adds an is_deleted flag instead of hard-deleting rows."""

    is_deleted = Column(Boolean, default=False, nullable=False)


# ── Cross-dialect UUID column ────────────────────────────────────────────
class GUID(TypeDecorator):
    """Platform-independent UUID type. Uses String(36) on all dialects."""

    impl = String(36)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            return str(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            return str(value)
        return value


def new_uuid():
    return str(uuid.uuid4())


# ── Cross-dialect JSON column ────────────────────────────────────────────
# sqlalchemy.JSON works on both PG and SQLite
PortableJSON = JSON
