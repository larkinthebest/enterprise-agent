"""Embedding service — wraps OpenAI text-embedding-3-small."""

from __future__ import annotations

import logging
import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

EMBED_URL = "https://api.openai.com/v1/embeddings"


async def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a batch of texts via OpenAI API. Returns list of float vectors."""
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            EMBED_URL,
            headers={"Authorization": f"Bearer {settings.openai_api_key}"},
            json={
                "model": settings.openai_embedding_model,
                "input": texts,
            },
        )
        resp.raise_for_status()
        data = resp.json()
    return [item["embedding"] for item in data["data"]]


async def embed_query(text: str) -> list[float]:
    """Embed a single query string."""
    vecs = await embed_texts([text])
    return vecs[0]
