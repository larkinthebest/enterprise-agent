"""Audit endpoints — list audit log entries (admin only)."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models.audit_log import AuditLog
from app.db.models.user import User
from app.api.deps import require_admin

router = APIRouter()
logger = logging.getLogger(__name__)


class AuditLogOut(BaseModel):
    id: str
    trace_id: str
    actor: str
    action: str
    resource: str | None = None
    payload: object | None = None
    status: str
    error_detail: str | None = None
    created_at: str

    model_config = {"from_attributes": True}


@router.get("/logs", response_model=list[AuditLogOut])
def list_audit_logs(
    trace_id: str | None = Query(None, description="Filter by trace_id"),
    actor: str | None = Query(None, description="Filter by actor username"),
    limit: int = Query(50, ge=1, le=500),
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """List audit log entries (admin only)."""
    query = db.query(AuditLog)
    if trace_id:
        query = query.filter(AuditLog.trace_id == trace_id)
    if actor:
        query = query.filter(AuditLog.actor == actor)

    logs = query.order_by(AuditLog.created_at.desc()).limit(limit).all()
    return [
        AuditLogOut(
            id=str(log.id),
            trace_id=log.trace_id,
            actor=log.actor,
            action=log.action,
            resource=log.resource,
            payload=log.payload,
            status=log.status,
            error_detail=log.error_detail,
            created_at=log.created_at.isoformat() if log.created_at else "",
        )
        for log in logs
    ]
