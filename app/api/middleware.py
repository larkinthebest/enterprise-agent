"""Request-ID middleware — injects a trace_id into every request context."""

import uuid
import time
import logging

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import current_trace_id

logger = logging.getLogger(__name__)


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Attach a unique trace_id to every request and measure latency."""

    async def dispatch(self, request: Request, call_next) -> Response:
        trace_id = request.headers.get("X-Trace-Id", f"tr_{uuid.uuid4().hex}")
        token = current_trace_id.set(trace_id)
        start = time.perf_counter()

        try:
            response: Response = await call_next(request)
            elapsed = round((time.perf_counter() - start) * 1000, 2)

            response.headers["X-Trace-Id"] = trace_id
            logger.info(
                "request completed",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status": response.status_code,
                    "elapsed_ms": elapsed,
                },
            )
            return response
        finally:
            current_trace_id.reset(token)
