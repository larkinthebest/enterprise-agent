"""RAG lookup node — retrieves context from the knowledge base."""

from __future__ import annotations

import logging
from app.agent.state import AgentState
from app.services.retriever import retrieve_context

logger = logging.getLogger(__name__)


async def rag_lookup_node(state: AgentState) -> AgentState:
    """Retrieve relevant KB articles based on the request and entities."""
    logger.info("rag_lookup_node: start", extra={"trace_id": state.trace_id})

    query = f"{state.request_text} {' '.join(state.entities)}"

    try:
        context = await retrieve_context(query, top_k=5)
        state.rag_context = context
        logger.info("rag_lookup_node: done", extra={"chunks": len(context)})
    except Exception as exc:
        logger.warning("rag_lookup_node: retrieval failed, continuing without context", extra={"error": str(exc)})
        state.rag_context = []

    return state
