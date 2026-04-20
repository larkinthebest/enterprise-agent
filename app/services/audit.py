"""Audit service — write and query immutable audit log entries."""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.orm import Session

from app.db.models.audit_log import AuditLog

logger = logging.getLogger(__name__)


def log_audit(
    db: Session,
    trace_id: str,
    actor: str,
    action: str,
    resource: str | None = None,
    payload: dict[str, Any] | None = None,
    status: str = "success",
    error_detail: str | None = None,
) -> None:
    """Write an audit entry. Fire-and-forget — never raises."""
    try:
        entry = AuditLog(
            trace_id=trace_id,
            actor=actor,
            action=action,
            resource=resource,
            payload=payload,
            status=status,
            error_detail=error_detail,
        )
        db.add(entry)
        db.commit()
    except Exception as exc:
        logger.error(f"Audit log write failed: {exc}")
        db.rollback()
