"""Document ingestion endpoint — seed the Qdrant KB with articles."""

from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.api.deps import require_operator
from app.db.models.user import User
from app.services.vector_store import get_qdrant_client, ensure_collection, COLLECTION_NAME
from app.services.embeddings import embed_texts
from qdrant_client.models import PointStruct

router = APIRouter()
logger = logging.getLogger(__name__)


class DocumentIn(BaseModel):
    title: str
    content: str
    category: str | None = None
    tags: list[str] = []


class BulkIngestRequest(BaseModel):
    documents: list[DocumentIn]


class IngestResponse(BaseModel):
    ingested: int
    ids: list[str]


@router.post("/ingest", response_model=IngestResponse, status_code=status.HTTP_201_CREATED)
async def ingest_documents(
    body: BulkIngestRequest,
    _user: User = Depends(require_operator),
):
    """Embed and store documents in Qdrant (operator+ only)."""
    if not body.documents:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No documents provided")

    ensure_collection()
    client = get_qdrant_client()

    texts = [f"{d.title}\n\n{d.content}" for d in body.documents]
    vectors = await embed_texts(texts)

    points = []
    ids = []
    for doc, vec in zip(body.documents, vectors):
        pid = str(uuid.uuid4())
        ids.append(pid)
        points.append(
            PointStruct(
                id=pid,
                vector=vec,
                payload={
                    "title": doc.title,
                    "content": doc.content,
                    "category": doc.category,
                    "tags": doc.tags,
                },
            )
        )

    client.upsert(collection_name=COLLECTION_NAME, points=points)
    logger.info("Documents ingested", extra={"count": len(points)})

    return IngestResponse(ingested=len(points), ids=ids)
