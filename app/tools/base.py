"""Base tool class — structured schema, retry, timeout, fallback."""

from __future__ import annotations

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any

from pydantic import BaseModel

from app.core.config import settings

logger = logging.getLogger(__name__)


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ToolSchema(BaseModel):
    """Metadata describing a tool for the LLM and for auditing."""
    name: str
    description: str
    risk_level: RiskLevel = RiskLevel.LOW
    parameters: dict[str, Any]
    returns: dict[str, Any] | None = None


class ToolResult(BaseModel):
    tool_name: str
    success: bool
    data: Any = None
    error: str | None = None
    elapsed_ms: float = 0


class BaseTool(ABC):
    """Every enterprise tool inherits from this."""

    name: str
    description: str
    risk_level: RiskLevel = RiskLevel.LOW

    @abstractmethod
    def get_schema(self) -> ToolSchema:
        ...

    @abstractmethod
    async def _execute(self, **kwargs: Any) -> Any:
        ...

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Execute with retry + timeout + fallback."""
        retries = settings.tool_retry_attempts
        delay = settings.tool_retry_delay_seconds
        timeout = settings.request_timeout_seconds

        last_error: str | None = None
        for attempt in range(1, retries + 1):
            start = time.perf_counter()
            try:
                result = await asyncio.wait_for(
                    self._execute(**kwargs),
                    timeout=timeout,
                )
                elapsed = round((time.perf_counter() - start) * 1000, 2)
                logger.info(
                    "tool executed",
                    extra={"tool": self.name, "attempt": attempt, "elapsed_ms": elapsed},
                )
                return ToolResult(
                    tool_name=self.name,
                    success=True,
                    data=result,
                    elapsed_ms=elapsed,
                )
            except asyncio.TimeoutError:
                last_error = f"Timeout after {timeout}s"
                logger.warning("tool timeout", extra={"tool": self.name, "attempt": attempt})
            except Exception as exc:
                last_error = str(exc)
                logger.warning(
                    "tool error",
                    extra={"tool": self.name, "attempt": attempt, "error": last_error},
                )
            if attempt < retries:
                await asyncio.sleep(delay * attempt)  # linear backoff

        # ── Fallback ─────────────────────────────────────────────────────
        fallback = await self._fallback(**kwargs)
        if fallback is not None:
            return ToolResult(
                tool_name=self.name,
                success=True,
                data=fallback,
                error=f"Used fallback after {retries} failures: {last_error}",
            )
        return ToolResult(
            tool_name=self.name,
            success=False,
            error=f"All {retries} attempts failed: {last_error}",
        )

    async def _fallback(self, **kwargs: Any) -> Any | None:
        """Override to provide degraded-mode data when the tool is unreachable."""
        return None

    @property
    def requires_approval(self) -> bool:
        return self.risk_level in (RiskLevel.MEDIUM, RiskLevel.HIGH)
