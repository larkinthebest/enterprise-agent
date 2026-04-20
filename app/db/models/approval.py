"""Approval request model — human-in-the-loop gate for risky actions."""

import enum

from sqlalchemy import Column, String, Text, Enum as SAEnum, ForeignKey, DateTime

from app.db.base import Base, TimestampMixin, GUID, PortableJSON, new_uuid


class ApprovalStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    TIMED_OUT = "timed_out"


class ApprovalRequest(TimestampMixin, Base):
    __tablename__ = "approval_requests"

    id = Column(GUID, primary_key=True, default=new_uuid)
    run_id = Column(GUID, ForeignKey("agent_runs.id"), nullable=False, index=True)
    action_name = Column(String(200), nullable=False)
    action_payload = Column(PortableJSON, nullable=True)
    risk_reason = Column(Text, nullable=True)
    status = Column(SAEnum(ApprovalStatus), nullable=False, default=ApprovalStatus.PENDING)
    reviewer_id = Column(GUID, ForeignKey("users.id"), nullable=True)
    reviewer_comment = Column(Text, nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
