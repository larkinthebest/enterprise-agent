"""LangGraph agent — wires all nodes into a conditional state graph."""

from __future__ import annotations

import logging

from langgraph.graph import StateGraph, END

from app.agent.state import AgentState
from app.agent.nodes.classify import classify_node
from app.agent.nodes.planner import planner_node
from app.agent.nodes.rag_lookup import rag_lookup_node
from app.agent.nodes.tool_executor import tool_executor_node
from app.agent.nodes.approval_gate import approval_gate_node
from app.agent.nodes.validator import validator_node
from app.agent.nodes.error_handler import error_handler_node

logger = logging.getLogger(__name__)


def _route_after_plan(state: AgentState) -> str:
    """After planning, decide whether to go to RAG or directly to tools."""
    if state.has_error:
        return "error_handler"
    # Always try RAG lookup for context enrichment
    return "rag_lookup"


def _route_after_tools(state: AgentState) -> str:
    """After tool execution, check if approval is needed or proceed to validation."""
    if state.has_error:
        return "error_handler"
    if state.pending_approval:
        return "approval_gate"
    return "validator"


def _route_after_approval(state: AgentState) -> str:
    """After the approval gate, decide next step."""
    if state.pending_approval:
        # Still pending — stop the graph here (will be resumed via callback)
        return END
    # Approval resolved — go back to tool execution to complete remaining steps
    return "tool_executor"


def _route_after_error(state: AgentState) -> str:
    """After error handling, always end."""
    return END


def _route_after_validation(state: AgentState) -> str:
    """After validation, end."""
    return END


def build_agent_graph() -> StateGraph:
    """Construct the LangGraph state machine for the enterprise agent."""

    graph = StateGraph(AgentState)

    # ── Add nodes ────────────────────────────────────────────────────────
    graph.add_node("classify", classify_node)
    graph.add_node("planner", planner_node)
    graph.add_node("rag_lookup", rag_lookup_node)
    graph.add_node("tool_executor", tool_executor_node)
    graph.add_node("approval_gate", approval_gate_node)
    graph.add_node("validator", validator_node)
    graph.add_node("error_handler", error_handler_node)

    # ── Entry point ──────────────────────────────────────────────────────
    graph.set_entry_point("classify")

    # ── Edges ────────────────────────────────────────────────────────────
    graph.add_edge("classify", "planner")

    graph.add_conditional_edges("planner", _route_after_plan, {
        "rag_lookup": "rag_lookup",
        "error_handler": "error_handler",
    })

    graph.add_edge("rag_lookup", "tool_executor")

    graph.add_conditional_edges("tool_executor", _route_after_tools, {
        "approval_gate": "approval_gate",
        "validator": "validator",
        "error_handler": "error_handler",
    })

    graph.add_conditional_edges("approval_gate", _route_after_approval, {
        "tool_executor": "tool_executor",
        END: END,
    })

    graph.add_conditional_edges("validator", _route_after_validation, {
        END: END,
    })

    graph.add_conditional_edges("error_handler", _route_after_error, {
        END: END,
    })

    return graph


# ── Compiled graph (reusable) ────────────────────────────────────────────
agent_graph = build_agent_graph().compile()
