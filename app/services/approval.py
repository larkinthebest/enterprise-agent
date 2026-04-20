"""Approval service — business logic for the human-in-the-loop gate."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.db.models.approval import ApprovalRequest, ApprovalStatus
from app.db.models.agent_run import AgentRun, RunStatus

logger = logging.getLogger(__name__)


def list_pending_approvals(db: Session) -> list[ApprovalRequest]:
    return (
        db.query(ApprovalRequest)
        .filter(ApprovalRequest.status == ApprovalStatus.PENDING)
        .order_by(ApprovalRequest.created_at.desc())
        .all()
    )


def approve_request(db: Session, approval_id: str, reviewer_id: str, comment: str = "") -> ApprovalRequest:
    approval = db.query(ApprovalRequest).filter(ApprovalRequest.id == approval_id).first()
    if not approval:
        raise ValueError(f"Approval {approval_id} not found")
    if approval.status != ApprovalStatus.PENDING:
        raise ValueError(f"Approval {approval_id} already resolved ({approval.status.value})")

    approval.status = ApprovalStatus.APPROVED
    approval.reviewer_id = reviewer_id
    approval.reviewer_comment = comment
    approval.resolved_at = datetime.now(timezone.utc)
    db.commit()

    logger.info("Approval granted", extra={"approval_id": approval_id, "reviewer": reviewer_id})
    return approval


def reject_request(db: Session, approval_id: str, reviewer_id: str, comment: str = "") -> ApprovalRequest:
    approval = db.query(ApprovalRequest).filter(ApprovalRequest.id == approval_id).first()
    if not approval:
        raise ValueError(f"Approval {approval_id} not found")
    if approval.status != ApprovalStatus.PENDING:
        raise ValueError(f"Approval {approval_id} already resolved ({approval.status.value})")

    approval.status = ApprovalStatus.REJECTED
    approval.reviewer_id = reviewer_id
    approval.reviewer_comment = comment
    approval.resolved_at = datetime.now(timezone.utc)

    # Mark the run as failed
    run = db.query(AgentRun).filter(AgentRun.id == approval.run_id).first()
    if run:
        run.status = RunStatus.FAILED
        run.error_detail = f"Action rejected by reviewer: {comment}"

    db.commit()
    logger.info("Approval rejected", extra={"approval_id": approval_id, "reviewer": reviewer_id})
    return approval
