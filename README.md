# Enterprise Agent Orchestrator

A production-grade AI agent system for processing internal business requests. Built with **FastAPI**, **LangGraph**, **Qdrant**, **PostgreSQL**, **Redis**, and **Langfuse**.

## 🏗️ Architecture

```
User → FastAPI → Middleware (trace_id + RBAC)
                      ↓
              POST /api/v1/agent/run
                      ↓
              ┌─── LangGraph ───┐
              │  classify        │  ← Intent detection
              │  planner         │  ← Step-by-step plan
              │  rag_lookup      │  ← Knowledge base search (Qdrant)
              │  tool_executor   │  ← Enterprise tool calls
              │  approval_gate   │  ← Human-in-the-loop for risky actions
              │  validator       │  ← Output quality check
              │  error_handler   │  ← Failure recovery & rollback
              └──────────────────┘
                      ↓
              Response + Audit Log + Langfuse Trace
```

## ✨ Features

- **LangGraph Agent** — conditional state graph with classify → plan → execute → validate pipeline
- **11 Enterprise Mock Tools** — CRM, Ticketing, Calendar, Knowledge Base, Email with realistic data
- **RAG Pipeline** — Qdrant vector search with OpenAI embeddings
- **RBAC** — API-key based auth with Admin / Operator / Viewer roles
- **Human-in-the-loop** — Approval workflow for MEDIUM/HIGH risk actions
- **Prompt Injection Defense** — Input sanitisation for all tool arguments
- **Retry & Fallback** — Configurable retry policy with linear backoff and degraded-mode fallbacks
- **Langfuse Tracing** — Full trace visibility per agent run
- **Audit Log** — Immutable PostgreSQL audit trail
- **Timeout Handling** — Configurable timeouts on all tool executions
- **Trace IDs** — Every request gets a unique `trace_id` propagated through the entire pipeline

## 🚀 Quick Start

### 1. Clone & configure

```bash
cp env.example .env
# Edit .env — set your OPENAI_API_KEY
```

### 2. Start infrastructure

```bash
docker-compose up -d
```

This starts: PostgreSQL, Redis, Qdrant, Langfuse, and the FastAPI app.

### 3. Get your admin API key

Check the app logs for the auto-generated admin API key:
```bash
docker-compose logs app | grep api_key
```

### 4. Use the API

```bash
# Health check
curl http://localhost:8000/api/v1/health

# Who am I?
curl -H "X-Api-Key: YOUR_KEY" http://localhost:8000/api/v1/auth/me

# Run the agent
curl -X POST http://localhost:8000/api/v1/agent/run \
  -H "X-Api-Key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"request_text": "Create a summary of open customer escalations, check related KB articles, draft a reply, and create a follow-up task."}'
```

## 📡 API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/api/v1/health` | None | Deep health check (PG, Redis, Qdrant) |
| `GET` | `/api/v1/auth/me` | Any | Identify caller |
| `POST` | `/api/v1/auth/users` | Admin | Create user |
| `GET` | `/api/v1/auth/users` | Admin | List users |
| `POST` | `/api/v1/agent/run` | Operator+ | Submit business request |
| `POST` | `/api/v1/documents/ingest` | Operator+ | Ingest KB documents into Qdrant |
| `GET` | `/api/v1/approvals/pending` | Operator+ | List pending approvals |
| `POST` | `/api/v1/approvals/{id}/approve` | Any | Approve risky action |
| `POST` | `/api/v1/approvals/{id}/reject` | Any | Reject risky action |
| `GET` | `/api/v1/audit/logs` | Admin | Query audit trail |

## 🛠️ Tools

| Tool | Risk | Description |
|------|------|-------------|
| `crm_search_customers` | LOW | Search CRM by name or tier |
| `crm_get_escalations` | LOW | Get open customer escalations |
| `ticketing_list_tickets` | LOW | List support tickets |
| `ticketing_create_ticket` | MEDIUM | Create a ticket (requires approval) |
| `ticketing_update_ticket` | MEDIUM | Update ticket fields (requires approval) |
| `calendar_list_events` | LOW | List upcoming events |
| `calendar_create_event` | MEDIUM | Schedule a meeting (requires approval) |
| `kb_search_articles` | LOW | Search internal knowledge base |
| `kb_get_article` | LOW | Get full KB article |
| `email_draft` | LOW | Create email draft |
| `email_send` | HIGH | Send email (always requires approval) |

## 🧪 Testing

```bash
pip install -r requirements.txt
pytest tests/ -v
```

## 📁 Project Structure

```
app/
├── main.py              # FastAPI app + lifespan
├── core/                # Config, logging, ID generation
├── api/
│   ├── deps.py          # RBAC dependencies
│   ├── middleware.py     # Request-ID middleware
│   └── routes/          # All REST endpoints
├── db/
│   ├── session.py       # SQLAlchemy engine
│   ├── base.py          # Declarative base + mixins
│   └── models/          # User, AgentRun, AuditLog, Approval
├── tools/
│   ├── base.py          # Tool base class (retry, timeout, fallback)
│   ├── registry.py      # Auto-discovery registry
│   ├── sanitizer.py     # Prompt injection defense
│   └── *.py             # 5 mock enterprise integrations
├── services/
│   ├── vector_store.py  # Qdrant client
│   ├── embeddings.py    # OpenAI embeddings
│   ├── retriever.py     # RAG retriever
│   ├── tracing.py       # Langfuse integration
│   ├── audit.py         # Audit log writer
│   └── approval.py      # Approval business logic
└── agent/
    ├── state.py         # Pydantic state schema
    ├── graph.py         # LangGraph wiring
    └── nodes/           # classify, planner, rag, tools, approval, validator, error
```

## 🔧 Configuration

All settings via environment variables (see `.env.example`). Key settings:

- `OPENAI_API_KEY` — Required for LLM and embeddings
- `TOOL_RETRY_ATTEMPTS` — Number of retries per tool (default: 3)
- `REQUEST_TIMEOUT_SECONDS` — Tool execution timeout (default: 30s)
- `APPROVAL_TIMEOUT_SECONDS` — Approval expiry (default: 3600s)

## 📊 Monitoring

- **Langfuse** — http://localhost:3000 for full trace exploration
- **Audit Logs** — `GET /api/v1/audit/logs` for compliance trail
- **Health** — `GET /api/v1/health` for infrastructure status
