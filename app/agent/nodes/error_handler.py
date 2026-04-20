"""Error handler / rollback node — handles failures and records rollback actions."""

from __future__ import annotations

import logging
from app.agent.state import AgentState

logger = logging.getLogger(__name__)


async def error_handler_node(state: AgentState) -> AgentState:
    """
    Handle errors:
    - Log the failure
    - Record rollback actions for any completed write operations
    - Set a user-facing error message
    """
    if not state.has_error:
        return state

    logger.error(
        "error_handler_node: handling error",
        extra={"trace_id": state.trace_id, "error": state.error_detail},
    )

    # ── Collect rollback actions for completed WRITE steps ───────────────
    write_tools = {
        "ticketing_create_ticket",
        "ticketing_update_ticket",
        "calendar_create_event",
        "email_send",
    }
    for step in state.plan:
        if step.status == "completed" and step.tool_name in write_tools:
            state.rollback_actions.append(
                {
                    "step_id": step.step_id,
                    "tool": step.tool_name,
                    "action": "rollback_needed",
                    "original_args": step.tool_args,
                    "result": step.result,
                }
            )

    if state.rollback_actions:
        logger.warning(
            "error_handler_node: rollback actions recorded",
            extra={"count": len(state.rollback_actions)},
        )

    # ── Set error response ───────────────────────────────────────────────
    state.final_answer = (
        f"⚠️ The agent encountered an error and could not complete your request.\n\n"
        f"**Error:** {state.error_detail}\n\n"
        f"**Completed steps:** {sum(1 for s in state.plan if s.status == 'completed')}/{len(state.plan)}\n"
        f"**Rollback actions:** {len(state.rollback_actions)} write operations may need manual review."
    )
    state.output_valid = False

    return state
