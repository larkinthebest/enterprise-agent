"""Calendar API mock — list events and create follow-up meetings."""

from __future__ import annotations

import asyncio
import random
from datetime import datetime, timezone, timedelta
from typing import Any

from app.tools.base import BaseTool, ToolSchema, RiskLevel

_MOCK_EVENTS: list[dict] = [
    {
        "id": "EVT-001",
        "title": "Weekly Escalation Review",
        "start": "2026-04-21T10:00:00Z",
        "end": "2026-04-21T10:30:00Z",
        "attendees": ["ops-team", "cs-lead"],
    },
    {
        "id": "EVT-002",
        "title": "Acme Corp account sync",
        "start": "2026-04-21T14:00:00Z",
        "end": "2026-04-21T14:45:00Z",
        "attendees": ["j.smith@acme.com", "cs-lead"],
    },
    {
        "id": "EVT-003",
        "title": "Sprint planning",
        "start": "2026-04-22T09:00:00Z",
        "end": "2026-04-22T10:00:00Z",
        "attendees": ["eng-team"],
    },
]


class ListEventsTool(BaseTool):
    name = "calendar_list_events"
    description = "List upcoming calendar events for a team or user."
    risk_level = RiskLevel.LOW

    def get_schema(self) -> ToolSchema:
        return ToolSchema(
            name=self.name,
            description=self.description,
            risk_level=self.risk_level,
            parameters={
                "attendee": {"type": "string", "description": "Filter by attendee", "required": False},
                "days_ahead": {
                    "type": "integer",
                    "description": "How many days to look ahead (default 7)",
                    "required": False,
                },
            },
        )

    async def _execute(self, attendee: str | None = None, days_ahead: int = 7, **kw: Any) -> list[dict]:
        await asyncio.sleep(random.uniform(0.05, 0.1))
        results = _MOCK_EVENTS
        if attendee:
            results = [e for e in results if attendee.lower() in [a.lower() for a in e["attendees"]]]
        return results


class CreateEventTool(BaseTool):
    name = "calendar_create_event"
    description = "Create a new calendar event / follow-up meeting."
    risk_level = RiskLevel.MEDIUM

    def get_schema(self) -> ToolSchema:
        return ToolSchema(
            name=self.name,
            description=self.description,
            risk_level=self.risk_level,
            parameters={
                "title": {"type": "string", "required": True},
                "start": {"type": "string", "format": "datetime", "required": True},
                "duration_minutes": {"type": "integer", "required": False, "default": 30},
                "attendees": {"type": "array", "items": "string", "required": False},
            },
        )

    async def _execute(
        self,
        title: str,
        start: str | None = None,
        duration_minutes: int = 30,
        attendees: list[str] | None = None,
        **kw: Any,
    ) -> dict:
        await asyncio.sleep(random.uniform(0.1, 0.2))
        start_dt = datetime.now(timezone.utc) + timedelta(days=1) if not start else datetime.fromisoformat(start)
        end_dt = start_dt + timedelta(minutes=duration_minutes)
        event = {
            "id": f"EVT-{random.randint(100, 999)}",
            "title": title,
            "start": start_dt.isoformat(),
            "end": end_dt.isoformat(),
            "attendees": attendees or [],
        }
        _MOCK_EVENTS.append(event)
        return event
