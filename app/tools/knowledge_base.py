"""Document Knowledge Base API mock — articles search and retrieval."""

from __future__ import annotations

import asyncio
import random
from typing import Any

from app.tools.base import BaseTool, ToolSchema, RiskLevel

_MOCK_KB_ARTICLES: list[dict] = [
    {"id": "KB-001", "title": "Troubleshooting EU Region Latency", "category": "infrastructure", "excerpt": "Steps to diagnose and resolve latency spikes in the EU-WEST cluster …", "tags": ["latency", "eu", "infrastructure"]},
    {"id": "KB-002", "title": "Billing Reconciliation Process", "category": "billing", "excerpt": "How to reconcile invoice amounts with usage data and handle discrepancies …", "tags": ["billing", "invoices", "reconciliation"]},
    {"id": "KB-003", "title": "SSO Integration Guide (SAML & OIDC)", "category": "authentication", "excerpt": "Step-by-step guide for setting up SSO with SAML 2.0 or OpenID Connect …", "tags": ["sso", "authentication", "saml", "oidc"]},
    {"id": "KB-004", "title": "Data Export Best Practices", "category": "data", "excerpt": "Optimise large data exports: pagination, streaming, and timeout configuration …", "tags": ["export", "data", "performance"]},
    {"id": "KB-005", "title": "Compliance Reporting — Field Reference", "category": "compliance", "excerpt": "Full field reference for SOC2 and ISO-27001 compliance reports …", "tags": ["compliance", "soc2", "iso27001"]},
    {"id": "KB-006", "title": "Incident Response Runbook", "category": "operations", "excerpt": "Standard operating procedure for P1/P2 incidents including escalation paths …", "tags": ["incident", "runbook", "operations"]},
    {"id": "KB-007", "title": "Customer Escalation Handling Playbook", "category": "customer_success", "excerpt": "Best practices for managing and resolving customer escalations, SLA timelines …", "tags": ["escalation", "customer_success", "sla"]},
]


class SearchArticlesTool(BaseTool):
    name = "kb_search_articles"
    description = "Search the internal knowledge base for relevant articles."
    risk_level = RiskLevel.LOW

    def get_schema(self) -> ToolSchema:
        return ToolSchema(
            name=self.name,
            description=self.description,
            risk_level=self.risk_level,
            parameters={
                "query": {"type": "string", "description": "Free-text search query", "required": True},
                "category": {"type": "string", "required": False},
            },
        )

    async def _execute(self, query: str = "", category: str | None = None, **kw: Any) -> list[dict]:
        await asyncio.sleep(random.uniform(0.05, 0.15))
        q = query.lower()
        results = _MOCK_KB_ARTICLES
        if category:
            results = [a for a in results if a["category"] == category.lower()]
        # Simple keyword match across title, excerpt, tags
        if q:
            scored = []
            for a in results:
                haystack = f"{a['title']} {a['excerpt']} {' '.join(a['tags'])}".lower()
                if any(word in haystack for word in q.split()):
                    scored.append(a)
            results = scored
        return results


class GetArticleTool(BaseTool):
    name = "kb_get_article"
    description = "Retrieve a full KB article by ID."
    risk_level = RiskLevel.LOW

    def get_schema(self) -> ToolSchema:
        return ToolSchema(
            name=self.name,
            description=self.description,
            risk_level=self.risk_level,
            parameters={
                "article_id": {"type": "string", "required": True},
            },
        )

    async def _execute(self, article_id: str, **kw: Any) -> dict | None:
        await asyncio.sleep(random.uniform(0.03, 0.1))
        for a in _MOCK_KB_ARTICLES:
            if a["id"] == article_id:
                return {**a, "body": f"Full content of article {a['id']}: {a['excerpt']} [continued …]"}
        return {"error": f"Article {article_id} not found"}
