"""Tool executor node — runs plan steps, applying sanitisation and retry."""

from __future__ import annotations

import logging

from app.agent.state import AgentState
from app.tools.registry import tool_registry
from app.tools.sanitizer import sanitise_tool_input, SanitisationError

logger = logging.getLogger(__name__)


async def tool_executor_node(state: AgentState) -> AgentState:
    """Execute the next pending tool step in the plan."""
    logger.info("tool_executor_node: start", extra={"trace_id": state.trace_id})

    for step in state.plan:
        if step.status != "pending":
            continue
        if step.requires_approval and not state.pending_approval:
            # This step needs approval — hand off to approval gate
            state.pending_approval = True
            state.approval_action = step.tool_name or step.description
            state.approval_payload = step.tool_args
            logger.info("tool_executor_node: approval required", extra={"step": step.step_id, "tool": step.tool_name})
            return state

        if not step.tool_name:
            step.status = "completed"
            step.result = {"note": "No tool needed for this step"}
            continue

        tool = tool_registry.get(step.tool_name)
        if not tool:
            step.status = "failed"
            step.error = f"Tool '{step.tool_name}' not found in registry"
            logger.error("tool_executor_node: unknown tool", extra={"tool": step.tool_name})
            continue

        # ── Sanitise inputs ──────────────────────────────────────────────
        try:
            clean_args = sanitise_tool_input(step.tool_name, step.tool_args)
        except SanitisationError as exc:
            step.status = "failed"
            step.error = str(exc)
            state.has_error = True
            state.error_detail = str(exc)
            logger.warning("tool_executor_node: sanitisation failed", extra={"error": str(exc)})
            return state

        # ── Execute ──────────────────────────────────────────────────────
        step.status = "running"
        result = await tool.execute(**clean_args)
        if result.success:
            step.status = "completed"
            step.result = result.data
            state.tool_results.append(
                {
                    "step_id": step.step_id,
                    "tool": result.tool_name,
                    "data": result.data,
                    "elapsed_ms": result.elapsed_ms,
                }
            )
        else:
            step.status = "failed"
            step.error = result.error
            logger.error("tool_executor_node: tool failed", extra={"tool": step.tool_name, "error": result.error})

    logger.info("tool_executor_node: done", extra={"completed": sum(1 for s in state.plan if s.status == "completed")})
    return state
