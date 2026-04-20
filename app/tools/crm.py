"""CRM API mock — customer and escalation data."""

from __future__ import annotations

import asyncio
import random
from typing import Any

from app.tools.base import BaseTool, ToolSchema, RiskLevel


_MOCK_CUSTOMERS = [
    {"id": "C-1001", "name": "Acme Corp", "tier": "enterprise", "contact": "j.smith@acme.com"},
    {"id": "C-1002", "name": "GlobalTech", "tier": "premium", "contact": "a.jones@globaltech.io"},
    {"id": "C-1003", "name": "StartUp Inc", "tier": "standard", "contact": "m.lee@startup.co"},
    {"id": "C-1004", "name": "MegaRetail", "tier": "enterprise", "contact": "r.wang@megaretail.com"},
    {"id": "C-1005", "name": "FinServ Ltd", "tier": "premium", "contact": "d.chen@finserv.uk"},
]

_MOCK_ESCALATIONS = [
    {
        "id": "ESC-4001",
        "customer_id": "C-1001",
        "subject": "Production outage in EU region",
        "severity": "critical",
        "status": "open",
        "created": "2026-04-18T09:12:00Z",
    },
    {
        "id": "ESC-4002",
        "customer_id": "C-1002",
        "subject": "Billing discrepancy Q1",
        "severity": "high",
        "status": "open",
        "created": "2026-04-17T14:30:00Z",
    },
    {
        "id": "ESC-4003",
        "customer_id": "C-1001",
        "subject": "SSO integration failure",
        "severity": "medium",
        "status": "open",
        "created": "2026-04-16T11:00:00Z",
    },
    {
        "id": "ESC-4004",
        "customer_id": "C-1004",
        "subject": "Data export timeout",
        "severity": "high",
        "status": "open",
        "created": "2026-04-15T08:45:00Z",
    },
    {
        "id": "ESC-4005",
        "customer_id": "C-1005",
        "subject": "Compliance report missing fields",
        "severity": "medium",
        "status": "in_progress",
        "created": "2026-04-14T16:20:00Z",
    },
]


class SearchCustomersTool(BaseTool):
    name = "crm_search_customers"
    description = "Search CRM for customers by name or tier."
    risk_level = RiskLevel.LOW

    def get_schema(self) -> ToolSchema:
        return ToolSchema(
            name=self.name,
            description=self.description,
            risk_level=self.risk_level,
            parameters={"query": {"type": "string", "description": "Name or tier to search"}},
            returns={"type": "array", "items": "Customer"},
        )

    async def _execute(self, query: str = "", **kw: Any) -> list[dict]:
        await asyncio.sleep(random.uniform(0.05, 0.15))  # simulate latency
        q = query.lower()
        return [c for c in _MOCK_CUSTOMERS if q in c["name"].lower() or q in c["tier"]]


class GetEscalationsTool(BaseTool):
    name = "crm_get_escalations"
    description = "Retrieve open customer escalations, optionally filtered by customer_id or severity."
    risk_level = RiskLevel.LOW

    def get_schema(self) -> ToolSchema:
        return ToolSchema(
            name=self.name,
            description=self.description,
            risk_level=self.risk_level,
            parameters={
                "customer_id": {"type": "string", "description": "Optional customer ID filter", "required": False},
                "severity": {
                    "type": "string",
                    "description": "Optional severity filter (critical|high|medium|low)",
                    "required": False,
                },
                "status": {"type": "string", "description": "Optional status filter", "required": False},
            },
            returns={"type": "array", "items": "Escalation"},
        )

    async def _execute(
        self, customer_id: str | None = None, severity: str | None = None, status: str | None = None, **kw: Any
    ) -> list[dict]:
        await asyncio.sleep(random.uniform(0.05, 0.15))
        results = _MOCK_ESCALATIONS
        if customer_id:
            results = [e for e in results if e["customer_id"] == customer_id]
        if severity:
            results = [e for e in results if e["severity"] == severity.lower()]
        if status:
            results = [e for e in results if e["status"] == status.lower()]
        return results
