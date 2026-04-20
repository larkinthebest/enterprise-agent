"""Classifier node — determines the intent and extracts entities from the request."""

from __future__ import annotations

import json
import logging

import httpx

from app.agent.state import AgentState, Intent
from app.core.config import settings

logger = logging.getLogger(__name__)

CLASSIFY_SYSTEM_PROMPT = """You are an intent classifier for an enterprise agent.
Given a user request, return a JSON object with:
- "intent": one of "query", "action", "mixed"
- "entities": list of key entities/topics mentioned

Respond ONLY with valid JSON, no markdown fences."""


async def classify_node(state: AgentState) -> AgentState:
    """Classify the user's request into intent and entities."""
    logger.info("classify_node: start", extra={"trace_id": state.trace_id})

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {settings.openai_api_key}"},
            json={
                "model": settings.openai_model,
                "temperature": 0,
                "messages": [
                    {"role": "system", "content": CLASSIFY_SYSTEM_PROMPT},
                    {"role": "user", "content": state.request_text},
                ],
            },
        )
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]

    try:
        parsed = json.loads(content)
        state.intent = Intent(parsed.get("intent", "unknown"))
        state.entities = parsed.get("entities", [])
    except (json.JSONDecodeError, ValueError):
        logger.warning("classify_node: failed to parse LLM response", extra={"raw": content})
        state.intent = Intent.MIXED
        state.entities = []

    logger.info("classify_node: done", extra={"intent": state.intent.value, "entities": state.entities})
    return state
