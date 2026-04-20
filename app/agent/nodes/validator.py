"""Validator node — validates the agent's final output before returning."""

from __future__ import annotations

import json
import logging

import httpx

from app.agent.state import AgentState
from app.core.config import settings

logger = logging.getLogger(__name__)

VALIDATOR_SYSTEM_PROMPT = """You are a quality validator for an enterprise agent's output.

Check the final answer for:
1. Completeness — does it address the user's original request?
2. Accuracy — are the referenced data/IDs consistent with the tool results?
3. Professionalism — is the tone appropriate for an enterprise setting?

Return JSON:
{
  "valid": true/false,
  "errors": ["list of issues found, if any"]
}

Respond ONLY with valid JSON, no markdown fences."""


async def validator_node(state: AgentState) -> AgentState:
    """Validate the final answer for quality and accuracy."""
    if state.has_error or state.pending_approval:
        return state

    logger.info("validator_node: start", extra={"trace_id": state.trace_id})

    # ── Build the final answer if not already set ────────────────────────
    if not state.final_answer:
        state = await _generate_final_answer(state)

    # ── Validate ─────────────────────────────────────────────────────────
    user_msg = (
        f"Original request: {state.request_text}\n\n"
        f"Tool results: {json.dumps(state.tool_results, default=str)[:3000]}\n\n"
        f"Final answer:\n{state.final_answer}"
    )

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.openai_api_key}"},
                json={
                    "model": settings.openai_model,
                    "temperature": 0,
                    "messages": [
                        {"role": "system", "content": VALIDATOR_SYSTEM_PROMPT},
                        {"role": "user", "content": user_msg},
                    ],
                },
            )
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]

        parsed = json.loads(content)
        state.output_valid = parsed.get("valid", False)
        state.validation_errors = parsed.get("errors", [])
    except Exception as exc:
        logger.warning("validator_node: validation call failed", extra={"error": str(exc)})
        state.output_valid = True  # fail-open for now
        state.validation_errors = []

    logger.info("validator_node: done", extra={"valid": state.output_valid, "errors": state.validation_errors})
    return state


async def _generate_final_answer(state: AgentState) -> AgentState:
    """Synthesise tool results + RAG context into a final user-facing answer."""
    rag_summary = ""
    if state.rag_context:
        rag_summary = "Relevant knowledge base articles:\n" + "\n".join(
            f"- [{c.get('title', 'N/A')}] {c.get('content', '')[:200]}" for c in state.rag_context
        )

    tool_summary = "Tool execution results:\n" + "\n".join(
        f"- Step {tr['step_id']} ({tr['tool']}): {json.dumps(tr['data'], default=str)[:500]}"
        for tr in state.tool_results
    )

    prompt = f"""Synthesise a professional answer for the user.

User request: {state.request_text}

{rag_summary}

{tool_summary}

Provide a clear, structured, enterprise-grade response."""

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {settings.openai_api_key}"},
            json={
                "model": settings.openai_model,
                "temperature": 0.3,
                "messages": [
                    {"role": "system", "content": "You are a helpful enterprise assistant."},
                    {"role": "user", "content": prompt},
                ],
            },
        )
        resp.raise_for_status()
        state.final_answer = resp.json()["choices"][0]["message"]["content"]

    return state
