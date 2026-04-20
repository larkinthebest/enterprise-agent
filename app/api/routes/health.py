"""Health-check endpoint — verifies connectivity to Postgres, Redis, Qdrant."""

import logging

from fastapi import APIRouter, status
from pydantic import BaseModel

from app.core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


class ComponentHealth(BaseModel):
    status: str  # "ok" | "degraded" | "down"
    detail: str | None = None


class HealthResponse(BaseModel):
    status: str
    postgres: ComponentHealth
    redis: ComponentHealth
    qdrant: ComponentHealth


def _check_postgres() -> ComponentHealth:
    try:
        from app.db.session import get_engine
        with get_engine().connect() as conn:
            conn.execute(__import__("sqlalchemy").text("SELECT 1"))
        return ComponentHealth(status="ok")
    except Exception as exc:
        return ComponentHealth(status="down", detail=str(exc)[:200])


def _check_redis() -> ComponentHealth:
    try:
        import redis as _redis
        r = _redis.Redis(host=settings.redis_host, port=settings.redis_port, socket_timeout=2)
        r.ping()
        return ComponentHealth(status="ok")
    except Exception as exc:
        return ComponentHealth(status="down", detail=str(exc)[:200])


def _check_qdrant() -> ComponentHealth:
    try:
        from qdrant_client import QdrantClient
        client = QdrantClient(url=settings.qdrant_url, timeout=2)
        client.get_collections()
        return ComponentHealth(status="ok")
    except Exception as exc:
        return ComponentHealth(status="down", detail=str(exc)[:200])


@router.get("/health", response_model=HealthResponse)
def health():
    """Deep health-check across all infrastructure dependencies."""
    pg = _check_postgres()
    rd = _check_redis()
    qd = _check_qdrant()

    components = [pg, rd, qd]
    if all(c.status == "ok" for c in components):
        overall = "healthy"
    elif any(c.status == "down" for c in components):
        overall = "degraded"
    else:
        overall = "degraded"

    return HealthResponse(status=overall, postgres=pg, redis=rd, qdrant=qd)
