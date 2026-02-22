"""Tests for OrchestratorState (EF-W005)."""

import pytest
from wanda.workflows.state import OrchestratorState, AgentResponse


def test_agent_response_is_dict():
    """AgentResponse is a TypedDict — access values via dict keys."""
    r: AgentResponse = {"success": True, "latency_ms": 0}
    assert r["success"] is True
    assert r.get("error") is None


def test_agent_response_failure():
    r: AgentResponse = {"success": False, "error": "timeout", "latency_ms": 0}
    assert not r["success"]
    assert r["error"] == "timeout"


def test_orchestrator_state_is_dict_like():
    state: OrchestratorState = {
        "query": "como esta o paciente",
        "patient_id": "p123",
        "workflow_id": "wf-1",
        "workflow_name": "clinical_analysis",
        "iterations": 0,
        "max_iterations": 3,
    }
    assert state["query"] == "como esta o paciente"
    assert state["patient_id"] == "p123"
    assert state["iterations"] == 0


def test_orchestrator_state_optional_fields():
    # total=False means all fields are optional
    state: OrchestratorState = {"query": "test"}
    assert state.get("ips") is None
    assert state.get("synthesis") is None
    assert state.get("error") is None


def test_agent_response_with_data():
    r: AgentResponse = {"success": True, "data": {"answer": "ok"}, "latency_ms": 150}
    assert r["latency_ms"] == 150
    assert r["data"]["answer"] == "ok"


def test_orchestrator_state_agent_responses():
    state: OrchestratorState = {
        "query": "test",
        "agent_responses": {
            "florence": {"success": True, "data": "resultado florence", "latency_ms": 200},
        },
    }
    assert state["agent_responses"]["florence"]["success"] is True
