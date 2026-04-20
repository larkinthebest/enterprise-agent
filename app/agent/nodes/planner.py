"""Planner node — generates a step-by-step execution plan using available tools."""

from __future__ import annotations

import json
import logging

import httpx

from app.agent.state import AgentState, PlanStep
from app.core.config import settings
from app.tools.registry import tool_registry

logger = logging.getLogger(__name__)

PLANNER_SYSTEM_PROMPT = """You are a planning agent for an enterprise system.

Given a user request, intent, entities, and available tools, produce a JSON array of execution steps.
Each step must have:
- "step_id": integer starting at 1
- "description": what this step does
- "tool_name": name of the tool to call (or null if no tool needed)
- "tool_args": dict of arguments for the tool

Available tools:
{tools}

Respond ONLY with a valid JSON array, no markdown fences."""


async def planner_node(state: AgentState) -> AgentState:
    """Build an execution plan based on request + intent + available tools."""
    logger.info("planner_node: start", extra={"trace_id": state.trace_id})

    tools_desc = json.dumps(
        [{"name": s.name, "description": s.description, "parameters": s.parameters}
         for s in tool_registry.get_schemas()],
        indent=2,
    )

    prompt = PLANNER_SYSTEM_PROMPT.format(tools=tools_desc)

    user_msg = (
        f"Request: {state.request_text}\n"
        f"Intent: {state.intent.value}\n"
        f"Entities: {', '.join(state.entities)}"
    )

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {settings.openai_api_key}"},
            json={
                "model": settings.openai_model,
                "temperature": 0,
                "messages": [
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": user_msg},
                ],
            },
        )
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]

    try:
        # Strip potential markdown fences
        clean = content.strip()
        if clean.startswith("```"):
            clean = clean.split("\n", 1)[1].rsplit("```", 1)[0]
        steps_raw = json.loads(clean)

        steps = []
        for raw in steps_raw:
            tool_name = raw.get("tool_name")
            tool = tool_registry.get(tool_name) if tool_name else None
            steps.append(PlanStep(
                step_id=raw["step_id"],
                description=raw["description"],
                tool_name=tool_name,
                tool_args=raw.get("tool_args", {}),
                requires_approval=tool.requires_approval if tool else False,
            ))
        state.plan = steps
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        logger.error("planner_node: failed to parse plan", extra={"error": str(exc), "raw": content})
        state.has_error = True
        state.error_detail = f"Planning failed: {exc}"

    logger.info("planner_node: done", extra={"steps": len(state.plan)})
    return state
