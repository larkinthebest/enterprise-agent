"""Agent API endpoint — POST /api/v1/agent/run."""

from __future__ import annotations

import logging
import time
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import require_operator
from app.core.ids import generate_trace_id
from app.core.logging import current_trace_id
from app.db.session import get_db
from app.db.models.agent_run import AgentRun, RunStatus
from app.db.models.approval import ApprovalRequest, ApprovalStatus
from app.db.models.user import User
from app.agent.state import AgentState
from app.agent.graph import agent_graph
from app.services.tracing import trace_agent_run
from app.services.audit import log_audit

router = APIRouter()
logger = logging.getLogger(__name__)


# ── Schemas ──────────────────────────────────────────────────────────────
class AgentRunRequest(BaseModel):
    request_text: str


class StepOut(BaseModel):
    step_id: int
    description: str
    tool_name: str | None = None
    status: str
    result: object = None
    error: str | None = None


class AgentRunResponse(BaseModel):
    run_id: str
    trace_id: str
    status: str
    plan: list[StepOut]
    final_answer: str
    output_valid: bool
    validation_errors: list[str]
    approval_required: bool = False
    approval_action: str | None = None
    elapsed_ms: float


# ── Endpoint ─────────────────────────────────────────────────────────────
@router.post("/run", response_model=AgentRunResponse)
async def run_agent(
    body: AgentRunRequest,
    user: User = Depends(require_operator),
    db: Session = Depends(get_db),
):
    """Submit a business request for the agent to process."""
    trace_id = generate_trace_id()
    token = current_trace_id.set(trace_id)
    run_id = str(uuid.uuid4())
    start = time.perf_counter()

    # ── Persist run ──────────────────────────────────────────────────────
    db_run = AgentRun(
        id=run_id,
        trace_id=trace_id,
        user_id=user.id,
        request_text=body.request_text,
        status=RunStatus.RUNNING,
    )
    db.add(db_run)
    db.commit()

    log_audit(db, trace_id, user.username, "agent.run.started", payload={"request": body.request_text[:500]})

    try:
        # ── Build initial state ──────────────────────────────────────────
        initial_state = AgentState(
            trace_id=trace_id,
            run_id=run_id,
            user_id=str(user.id),
            user_role=user.role.value,
            request_text=body.request_text,
        )

        # ── Run the graph ────────────────────────────────────────────────
        with trace_agent_run(trace_id, run_id, body.request_text):
            final_state = await agent_graph.ainvoke(initial_state)

        # If the graph returns a dict, convert it
        if isinstance(final_state, dict):
            final_state = AgentState(**final_state)

        elapsed = round((time.perf_counter() - start) * 1000, 2)

        # ── Handle approval pause ────────────────────────────────────────
        if final_state.pending_approval:
            db_run.status = RunStatus.AWAITING_APPROVAL
            db_run.plan = [s.model_dump() for s in final_state.plan]
            db.commit()

            # Create approval request
            approval = ApprovalRequest(
                run_id=run_id,
                action_name=final_state.approval_action,
                action_payload=final_state.approval_payload,
                risk_reason=f"Tool '{final_state.approval_action}' requires human approval",
                status=ApprovalStatus.PENDING,
            )
            db.add(approval)
            db.commit()

            log_audit(
                db,
                trace_id,
                user.username,
                "agent.run.awaiting_approval",
                payload={"action": final_state.approval_action},
            )

            return AgentRunResponse(
                run_id=run_id,
                trace_id=trace_id,
                status="awaiting_approval",
                plan=[StepOut(**s.model_dump()) for s in final_state.plan],
                final_answer="⏳ Run paused — awaiting human approval for a risky action.",
                output_valid=False,
                validation_errors=[],
                approval_required=True,
                approval_action=final_state.approval_action,
                elapsed_ms=elapsed,
            )

        # ── Completed ────────────────────────────────────────────────────
        final_status = RunStatus.COMPLETED if not final_state.has_error else RunStatus.FAILED
        db_run.status = final_status
        db_run.plan = [s.model_dump() for s in final_state.plan]
        db_run.result = {"final_answer": final_state.final_answer, "tool_results": final_state.tool_results}
        db_run.elapsed_ms = str(elapsed)
        if final_state.has_error:
            db_run.error_detail = final_state.error_detail
        db.commit()

        log_audit(db, trace_id, user.username, f"agent.run.{final_status.value}", payload={"elapsed_ms": elapsed})

        return AgentRunResponse(
            run_id=run_id,
            trace_id=trace_id,
            status=final_status.value,
            plan=[StepOut(**s.model_dump()) for s in final_state.plan],
            final_answer=final_state.final_answer,
            output_valid=final_state.output_valid,
            validation_errors=final_state.validation_errors,
            elapsed_ms=elapsed,
        )

    except Exception as exc:
        elapsed = round((time.perf_counter() - start) * 1000, 2)
        logger.exception("Agent run failed")
        db_run.status = RunStatus.FAILED
        db_run.error_detail = str(exc)[:2000]
        db_run.elapsed_ms = str(elapsed)
        db.commit()

        log_audit(db, trace_id, user.username, "agent.run.error", status="error", error_detail=str(exc)[:500])

        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)[:500])
    finally:
        current_trace_id.reset(token)
