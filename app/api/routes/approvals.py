"""Approval endpoints — list pending, approve, reject."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models.user import User
from app.api.deps import CurrentUser, require_operator
from app.services.approval import list_pending_approvals, approve_request, reject_request
from app.services.audit import log_audit
from app.core.logging import current_trace_id

router = APIRouter()
logger = logging.getLogger(__name__)


class ApprovalOut(BaseModel):
    id: str
    run_id: str
    action_name: str
    action_payload: object | None = None
    risk_reason: str | None = None
    status: str
    reviewer_comment: str | None = None

    model_config = {"from_attributes": True}


class ApprovalDecision(BaseModel):
    comment: str = ""


@router.get("/pending", response_model=list[ApprovalOut])
def get_pending(
    _user: User = Depends(require_operator),
    db: Session = Depends(get_db),
):
    """List all pending approval requests."""
    approvals = list_pending_approvals(db)
    return [
        ApprovalOut(
            id=str(a.id),
            run_id=str(a.run_id),
            action_name=a.action_name,
            action_payload=a.action_payload,
            risk_reason=a.risk_reason,
            status=a.status.value,
        )
        for a in approvals
    ]


@router.post("/{approval_id}/approve", response_model=ApprovalOut)
def approve(
    approval_id: str,
    body: ApprovalDecision,
    user: CurrentUser,
    db: Session = Depends(get_db),
):
    """Approve a pending action."""
    try:
        a = approve_request(db, approval_id, str(user.id), body.comment)
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc))

    log_audit(
        db,
        current_trace_id.get(),
        user.username,
        "approval.approved",
        resource=approval_id,
        payload={"comment": body.comment},
    )

    return ApprovalOut(
        id=str(a.id),
        run_id=str(a.run_id),
        action_name=a.action_name,
        action_payload=a.action_payload,
        risk_reason=a.risk_reason,
        status=a.status.value,
        reviewer_comment=a.reviewer_comment,
    )


@router.post("/{approval_id}/reject", response_model=ApprovalOut)
def reject(
    approval_id: str,
    body: ApprovalDecision,
    user: CurrentUser,
    db: Session = Depends(get_db),
):
    """Reject a pending action."""
    try:
        a = reject_request(db, approval_id, str(user.id), body.comment)
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc))

    log_audit(
        db,
        current_trace_id.get(),
        user.username,
        "approval.rejected",
        resource=approval_id,
        payload={"comment": body.comment},
    )

    return ApprovalOut(
        id=str(a.id),
        run_id=str(a.run_id),
        action_name=a.action_name,
        action_payload=a.action_payload,
        risk_reason=a.risk_reason,
        status=a.status.value,
        reviewer_comment=a.reviewer_comment,
    )
