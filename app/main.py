"""FastAPI application entry point with lifespan management."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import setup_logging
from app.api.middleware import RequestIdMiddleware
from app.api.routes import health, agent, auth, approvals, documents, audit
from app.db.session import get_engine
from app.db.base import Base


@asynccontextmanager
async def lifespan(application: FastAPI):
    """Startup / shutdown hooks."""
    setup_logging()
    logger = logging.getLogger(settings.app_name)

    # ── Startup ──────────────────────────────────────────────────────────
    logger.info("Creating database tables …")
    Base.metadata.create_all(bind=get_engine())

    logger.info("Application started", extra={"env": settings.app_env})
    yield

    # ── Shutdown ─────────────────────────────────────────────────────────
    logger.info("Shutting down …")
    if settings.app_env != "test":
        get_engine().dispose()


app = FastAPI(
    title="Enterprise Agent Orchestrator",
    version="0.1.0",
    description="LangGraph-powered agent for internal business request processing",
    lifespan=lifespan,
)

# ── Middleware ────────────────────────────────────────────────────────────
app.add_middleware(RequestIdMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ──────────────────────────────────────────────────────────────
app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(agent.router, prefix="/api/v1/agent", tags=["agent"])
app.include_router(approvals.router, prefix="/api/v1/approvals", tags=["approvals"])
app.include_router(documents.router, prefix="/api/v1/documents", tags=["documents"])
app.include_router(audit.router, prefix="/api/v1/audit", tags=["audit"])
