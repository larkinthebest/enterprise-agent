"""AgentRun model — tracks each end-to-end agent invocation."""

import enum

from sqlalchemy import Column, String, Text, Enum as SAEnum, ForeignKey

from app.db.base import Base, TimestampMixin, GUID, PortableJSON, new_uuid


class RunStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    AWAITING_APPROVAL = "awaiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class AgentRun(TimestampMixin, Base):
    __tablename__ = "agent_runs"

    id = Column(GUID, primary_key=True, default=new_uuid)
    trace_id = Column(String(64), nullable=False, index=True)
    user_id = Column(GUID, ForeignKey("users.id"), nullable=False)
    request_text = Column(Text, nullable=False)
    status = Column(SAEnum(RunStatus), nullable=False, default=RunStatus.PENDING)
    plan = Column(PortableJSON, nullable=True)
    result = Column(PortableJSON, nullable=True)
    error_detail = Column(Text, nullable=True)
    elapsed_ms = Column(String(20), nullable=True)
