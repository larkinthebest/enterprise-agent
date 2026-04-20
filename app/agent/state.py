"""Agent state — the Pydantic schema flowing through the LangGraph."""

from __future__ import annotations

from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


class Intent(str, Enum):
    QUERY = "query"
    ACTION = "action"
    MIXED = "mixed"
    UNKNOWN = "unknown"


class PlanStep(BaseModel):
    """One step in the agent's execution plan."""
    step_id: int
    description: str
    tool_name: str | None = None
    tool_args: dict[str, Any] = {}
    requires_approval: bool = False
    status: str = "pending"           # pending | running | completed | failed | skipped
    result: Any = None
    error: str | None = None


class AgentState(BaseModel):
    """Full state object passed between LangGraph nodes."""
    # ── Identity ─────────────────────────────────────────────────────────
    trace_id: str = ""
    run_id: str = ""
    user_id: str = ""
    user_role: str = ""

    # ── Input ────────────────────────────────────────────────────────────
    request_text: str = ""

    # ── Classification ───────────────────────────────────────────────────
    intent: Intent = Intent.UNKNOWN
    entities: list[str] = Field(default_factory=list)

    # ── Planning ─────────────────────────────────────────────────────────
    plan: list[PlanStep] = Field(default_factory=list)
    current_step_index: int = 0

    # ── RAG context ──────────────────────────────────────────────────────
    rag_context: list[dict[str, Any]] = Field(default_factory=list)

    # ── Tool results ─────────────────────────────────────────────────────
    tool_results: list[dict[str, Any]] = Field(default_factory=list)

    # ── Approval ─────────────────────────────────────────────────────────
    pending_approval: bool = False
    approval_action: str = ""
    approval_payload: dict[str, Any] = Field(default_factory=dict)

    # ── Output ───────────────────────────────────────────────────────────
    final_answer: str = ""
    output_valid: bool = False
    validation_errors: list[str] = Field(default_factory=list)

    # ── Error handling ───────────────────────────────────────────────────
    has_error: bool = False
    error_detail: str = ""
    rollback_actions: list[dict[str, Any]] = Field(default_factory=list)
