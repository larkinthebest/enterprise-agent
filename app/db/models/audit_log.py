"""Audit log model — immutable record of every significant action."""

from sqlalchemy import Column, String, Text, DateTime
from datetime import datetime, timezone

from app.db.base import Base, GUID, PortableJSON, new_uuid


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(GUID, primary_key=True, default=new_uuid)
    trace_id = Column(String(64), nullable=False, index=True)
    actor = Column(String(100), nullable=False)
    action = Column(String(200), nullable=False)
    resource = Column(String(200), nullable=True)
    payload = Column(PortableJSON, nullable=True)
    status = Column(String(20), nullable=False, default="success")
    error_detail = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
