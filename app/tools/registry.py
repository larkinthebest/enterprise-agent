"""Tool registry — discovers, validates, and exposes all available tools."""

from __future__ import annotations

import logging
from typing import Any

from app.tools.base import BaseTool, ToolSchema
from app.tools.crm import SearchCustomersTool, GetEscalationsTool
from app.tools.ticketing import ListTicketsTool, CreateTicketTool, UpdateTicketTool
from app.tools.calendar import ListEventsTool, CreateEventTool
from app.tools.knowledge_base import SearchArticlesTool, GetArticleTool
from app.tools.email import DraftEmailTool, SendEmailTool

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Singleton registry of all enterprise tools."""

    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}
        self._register_defaults()

    def _register_defaults(self) -> None:
        defaults: list[BaseTool] = [
            SearchCustomersTool(),
            GetEscalationsTool(),
            ListTicketsTool(),
            CreateTicketTool(),
            UpdateTicketTool(),
            ListEventsTool(),
            CreateEventTool(),
            SearchArticlesTool(),
            GetArticleTool(),
            DraftEmailTool(),
            SendEmailTool(),
        ]
        for tool in defaults:
            self.register(tool)

    def register(self, tool: BaseTool) -> None:
        if tool.name in self._tools:
            logger.warning(f"Tool '{tool.name}' already registered — overwriting")
        self._tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name} (risk={tool.risk_level.value})")

    def get(self, name: str) -> BaseTool | None:
        return self._tools.get(name)

    def list_tools(self) -> list[str]:
        return list(self._tools.keys())

    def get_schemas(self) -> list[ToolSchema]:
        return [t.get_schema() for t in self._tools.values()]

    def get_schemas_for_llm(self) -> list[dict[str, Any]]:
        """Return schemas formatted for the LLM's function-calling interface."""
        out = []
        for tool in self._tools.values():
            s = tool.get_schema()
            out.append({
                "type": "function",
                "function": {
                    "name": s.name,
                    "description": s.description,
                    "parameters": {
                        "type": "object",
                        "properties": s.parameters,
                    },
                },
            })
        return out


# Module-level singleton
tool_registry = ToolRegistry()
