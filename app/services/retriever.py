"""RAG retriever — embed query → Qdrant search → return context chunks."""

from __future__ import annotations

import logging
from typing import Any

from qdrant_client.models import ScoredPoint

from app.services.vector_store import get_qdrant_client, COLLECTION_NAME
from app.services.embeddings import embed_query

logger = logging.getLogger(__name__)


async def retrieve_context(query: str, top_k: int = 5) -> list[dict[str, Any]]:
    """
    Retrieve the most relevant KB chunks for a user query.

    Returns a list of dicts with keys: id, score, title, content, metadata.
    """
    vector = await embed_query(query)
    client = get_qdrant_client()

    results: list[ScoredPoint] = client.search(
        collection_name=COLLECTION_NAME,
        query_vector=vector,
        limit=top_k,
        with_payload=True,
    )

    context_chunks = []
    for hit in results:
        payload = hit.payload or {}
        context_chunks.append({
            "id": str(hit.id),
            "score": round(hit.score, 4),
            "title": payload.get("title", ""),
            "content": payload.get("content", ""),
            "metadata": {k: v for k, v in payload.items() if k not in ("title", "content")},
        })

    logger.info(
        "RAG retrieval complete",
        extra={"query_length": len(query), "hits": len(context_chunks)},
    )
    return context_chunks
