"""Unit tests for agent state and node logic."""

import pytest

from app.agent.state import AgentState, Intent, PlanStep


def test_initial_state_defaults():
    state = AgentState()
    assert state.intent == Intent.UNKNOWN
    assert state.plan == []
    assert state.has_error is False
    assert state.pending_approval is False


def test_plan_step_creation():
    step = PlanStep(
        step_id=1,
        description="Search for escalations",
        tool_name="crm_get_escalations",
        tool_args={"severity": "critical"},
    )
    assert step.status == "pending"
    assert step.requires_approval is False


def test_state_with_plan():
    state = AgentState(
        trace_id="tr_test",
        run_id="run_test",
        request_text="Get escalations",
        intent=Intent.QUERY,
        plan=[
            PlanStep(step_id=1, description="Get escalations", tool_name="crm_get_escalations"),
            PlanStep(step_id=2, description="Search KB", tool_name="kb_search_articles"),
        ],
    )
    assert len(state.plan) == 2
    assert state.plan[0].tool_name == "crm_get_escalations"


def test_state_error_handling():
    state = AgentState(
        has_error=True,
        error_detail="Tool timeout",
    )
    assert state.has_error
    assert "timeout" in state.error_detail.lower()


def test_state_approval_flow():
    state = AgentState(
        pending_approval=True,
        approval_action="ticketing_create_ticket",
        approval_payload={"title": "New ticket"},
    )
    assert state.pending_approval
    assert state.approval_action == "ticketing_create_ticket"
