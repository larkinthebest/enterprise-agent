"""Approval gate node — pauses execution when a risky action needs human sign-off."""

from __future__ import annotations

import logging

from app.agent.state import AgentState

logger = logging.getLogger(__name__)


async def approval_gate_node(state: AgentState) -> AgentState:
    """
    If pending_approval is True, mark the run as AWAITING_APPROVAL and
    return early. The graph will stop here until the approval callback
    resumes it.
    """
    logger.info(
        "approval_gate_node: checking",
        extra={
            "trace_id": state.trace_id,
            "pending": state.pending_approval,
            "action": state.approval_action,
        },
    )

    if state.pending_approval:
        logger.info("approval_gate_node: waiting for human approval")
        # The API layer persists this state and returns a 202.
        # When the reviewer approves, the graph is resumed.
        return state

    # No approval needed — continue
    return state
