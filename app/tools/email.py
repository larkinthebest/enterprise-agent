"""Email Draft API mock — draft and (mock) send emails."""

from __future__ import annotations

import asyncio
import random
import uuid
from typing import Any

from app.tools.base import BaseTool, ToolSchema, RiskLevel

_MOCK_DRAFTS: list[dict] = []


class DraftEmailTool(BaseTool):
    name = "email_draft"
    description = "Create an email draft (does NOT send). Read-only safe action."
    risk_level = RiskLevel.LOW

    def get_schema(self) -> ToolSchema:
        return ToolSchema(
            name=self.name,
            description=self.description,
            risk_level=self.risk_level,
            parameters={
                "to": {"type": "string", "required": True},
                "subject": {"type": "string", "required": True},
                "body": {"type": "string", "required": True},
                "cc": {"type": "string", "required": False},
            },
        )

    async def _execute(self, to: str, subject: str, body: str, cc: str | None = None, **kw: Any) -> dict:
        await asyncio.sleep(random.uniform(0.05, 0.15))
        draft = {
            "id": f"DRF-{uuid.uuid4().hex[:8]}",
            "to": to,
            "subject": subject,
            "body": body,
            "cc": cc,
            "status": "draft",
        }
        _MOCK_DRAFTS.append(draft)
        return draft


class SendEmailTool(BaseTool):
    name = "email_send"
    description = "Send a previously drafted email. HIGH-risk: leaves the system boundary."
    risk_level = RiskLevel.HIGH  # always requires approval

    def get_schema(self) -> ToolSchema:
        return ToolSchema(
            name=self.name,
            description=self.description,
            risk_level=self.risk_level,
            parameters={
                "draft_id": {"type": "string", "required": True},
            },
        )

    async def _execute(self, draft_id: str, **kw: Any) -> dict:
        await asyncio.sleep(random.uniform(0.1, 0.3))
        for draft in _MOCK_DRAFTS:
            if draft["id"] == draft_id:
                draft["status"] = "sent"
                return {"message": f"Email {draft_id} sent to {draft['to']}", "draft": draft}
        return {"error": f"Draft {draft_id} not found"}

    async def _fallback(self, **kwargs: Any) -> dict | None:
        return {"message": "Email service unavailable — draft saved for manual sending", "queued": True}
