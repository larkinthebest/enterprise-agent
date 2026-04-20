"""Langfuse tracing service — wraps the Langfuse SDK for trace lifecycle management."""

from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Any, Generator

from langfuse import Langfuse

from app.core.config import settings

logger = logging.getLogger(__name__)

_langfuse_client: Langfuse | None = None


def get_langfuse() -> Langfuse:
    """Lazily initialise the Langfuse client singleton."""
    global _langfuse_client
    if _langfuse_client is None:
        try:
            _langfuse_client = Langfuse(
                public_key=settings.langfuse_public_key,
                secret_key=settings.langfuse_secret_key,
                host=settings.langfuse_host,
            )
            logger.info("Langfuse client initialised")
        except Exception as exc:
            logger.warning(f"Langfuse init failed — tracing disabled: {exc}")
    return _langfuse_client


@contextmanager
def trace_agent_run(trace_id: str, run_id: str, request_text: str) -> Generator[Any, None, None]:
    """Context manager that wraps an agent run in a Langfuse trace."""
    lf = get_langfuse()
    trace = None
    if lf:
        try:
            trace = lf.trace(
                id=trace_id,
                name="agent_run",
                metadata={"run_id": run_id},
                input={"request_text": request_text},
            )
        except Exception as exc:
            logger.warning(f"Langfuse trace creation failed: {exc}")

    try:
        yield trace
    finally:
        if trace:
            try:
                trace.update(output={"status": "completed"})
                lf.flush()
            except Exception as exc:
                logger.warning(f"Langfuse trace flush failed: {exc}")


def trace_node(trace_id: str, node_name: str, input_data: dict, output_data: dict) -> None:
    """Log a single node execution as a Langfuse span."""
    lf = get_langfuse()
    if not lf:
        return
    try:
        lf.span(
            trace_id=trace_id,
            name=node_name,
            input=input_data,
            output=output_data,
        )
    except Exception as exc:
        logger.warning(f"Langfuse span failed: {exc}")
