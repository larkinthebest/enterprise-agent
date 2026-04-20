"""Ticketing API mock — list / create / update support tickets."""

from __future__ import annotations

import asyncio
import random
from datetime import datetime, timezone
from typing import Any

from app.tools.base import BaseTool, ToolSchema, RiskLevel

_MOCK_TICKETS: list[dict] = [
    {
        "id": "TKT-7001",
        "customer_id": "C-1001",
        "title": "EU region latency spike",
        "priority": "P1",
        "status": "open",
        "assignee": "ops-team",
        "created": "2026-04-18T09:15:00Z",
    },
    {
        "id": "TKT-7002",
        "customer_id": "C-1002",
        "title": "Invoice #4455 amount mismatch",
        "priority": "P2",
        "status": "open",
        "assignee": "billing-team",
        "created": "2026-04-17T14:35:00Z",
    },
    {
        "id": "TKT-7003",
        "customer_id": "C-1003",
        "title": "Feature request: bulk export",
        "priority": "P3",
        "status": "triaged",
        "assignee": "product-team",
        "created": "2026-04-16T10:00:00Z",
    },
    {
        "id": "TKT-7004",
        "customer_id": "C-1004",
        "title": "Data export timing out for large datasets",
        "priority": "P2",
        "status": "open",
        "assignee": "eng-team",
        "created": "2026-04-15T09:00:00Z",
    },
]


class ListTicketsTool(BaseTool):
    name = "ticketing_list_tickets"
    description = "List support tickets with optional filters."
    risk_level = RiskLevel.LOW

    def get_schema(self) -> ToolSchema:
        return ToolSchema(
            name=self.name,
            description=self.description,
            risk_level=self.risk_level,
            parameters={
                "customer_id": {"type": "string", "required": False},
                "status": {"type": "string", "required": False},
                "priority": {"type": "string", "required": False},
            },
        )

    async def _execute(
        self, customer_id: str | None = None, status: str | None = None, priority: str | None = None, **kw: Any
    ) -> list[dict]:
        await asyncio.sleep(random.uniform(0.05, 0.15))
        results = _MOCK_TICKETS
        if customer_id:
            results = [t for t in results if t["customer_id"] == customer_id]
        if status:
            results = [t for t in results if t["status"] == status.lower()]
        if priority:
            results = [t for t in results if t["priority"] == priority.upper()]
        return results


class CreateTicketTool(BaseTool):
    name = "ticketing_create_ticket"
    description = "Create a new support ticket. This is a write operation."
    risk_level = RiskLevel.MEDIUM  # requires approval

    def get_schema(self) -> ToolSchema:
        return ToolSchema(
            name=self.name,
            description=self.description,
            risk_level=self.risk_level,
            parameters={
                "customer_id": {"type": "string", "required": True},
                "title": {"type": "string", "required": True},
                "priority": {"type": "string", "enum": ["P1", "P2", "P3", "P4"], "required": True},
                "assignee": {"type": "string", "required": False},
                "description": {"type": "string", "required": False},
            },
        )

    async def _execute(
        self,
        customer_id: str,
        title: str,
        priority: str = "P3",
        assignee: str = "unassigned",
        description: str = "",
        **kw: Any,
    ) -> dict:
        await asyncio.sleep(random.uniform(0.1, 0.3))
        ticket = {
            "id": f"TKT-{random.randint(8000, 9999)}",
            "customer_id": customer_id,
            "title": title,
            "priority": priority,
            "status": "open",
            "assignee": assignee,
            "description": description,
            "created": datetime.now(timezone.utc).isoformat(),
        }
        _MOCK_TICKETS.append(ticket)
        return ticket


class UpdateTicketTool(BaseTool):
    name = "ticketing_update_ticket"
    description = "Update an existing ticket (status, assignee, priority)."
    risk_level = RiskLevel.MEDIUM

    def get_schema(self) -> ToolSchema:
        return ToolSchema(
            name=self.name,
            description=self.description,
            risk_level=self.risk_level,
            parameters={
                "ticket_id": {"type": "string", "required": True},
                "status": {"type": "string", "required": False},
                "assignee": {"type": "string", "required": False},
                "priority": {"type": "string", "required": False},
            },
        )

    async def _execute(self, ticket_id: str, **updates: Any) -> dict:
        await asyncio.sleep(random.uniform(0.05, 0.15))
        for ticket in _MOCK_TICKETS:
            if ticket["id"] == ticket_id:
                for k, v in updates.items():
                    if k in ticket and v is not None:
                        ticket[k] = v
                return ticket
        return {"error": f"Ticket {ticket_id} not found"}
