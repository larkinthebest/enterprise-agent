"""Qdrant vector store client singleton."""

from __future__ import annotations

import logging
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

from app.core.config import settings

logger = logging.getLogger(__name__)

COLLECTION_NAME = "enterprise_kb"
VECTOR_DIM = 1536  # text-embedding-3-small


def get_qdrant_client() -> QdrantClient:
    return QdrantClient(url=settings.qdrant_url, timeout=10)


def ensure_collection(client: QdrantClient | None = None) -> None:
    """Create the KB collection if it doesn't exist yet."""
    client = client or get_qdrant_client()
    collections = [c.name for c in client.get_collections().collections]
    if COLLECTION_NAME not in collections:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=VECTOR_DIM, distance=Distance.COSINE),
        )
        logger.info(f"Created Qdrant collection '{COLLECTION_NAME}'")
    else:
        logger.info(f"Qdrant collection '{COLLECTION_NAME}' already exists")
