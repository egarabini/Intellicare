"""Tests for WorkflowExecutor (EF-W005)."""

import asyncio
import pytest
from unittest.mock import MagicMock

from wanda.workflows.executor import WorkflowExecutor, WorkflowResult


@pytest.fixture
def executor():
    return WorkflowExecutor(timeout_seconds=10, max_iterations=3)


def test_executor_available_workflows_method_exists(executor):
    assert callable(executor.available_workflows)
    assert isinstance(executor.available_workflows(), list)


def test_executor_select_workflow_method_exists(executor):
    assert callable(executor.select_workflow)


def test_select_workflow_critical_takes_precedence(executor):
    import wanda.workflows.executor as exec_module
    original = exec_module._BUILDERS.copy()
    try:
        exec_module._BUILDERS = {
            "clinical_analysis": lambda: None,
            "patient_onboarding": lambda: None,
            "critical_alert": lambda: None,
        }
        name = executor.select_workflow(intent="anything", has_patient=True, is_critical=True)
        assert name == "critical_alert"
    finally:
        exec_module._BUILDERS = original


def test_select_workflow_clinical_intent(executor):
    import wanda.workflows.executor as exec_module
    original = exec_module._BUILDERS.copy()
    try:
        exec_module._BUILDERS = {
            "clinical_analysis": lambda: None,
            "patient_onboarding": lambda: None,
            "critical_alert": lambda: None,
        }
        name = executor.select_workflow(intent="analise clinica completa", has_patient=True, is_critical=False)
        assert name == "clinical_analysis"
    finally:
        exec_module._BUILDERS = original


def test_select_workflow_no_builders_returns_none(executor):
    import wanda.workflows.executor as exec_module
    original = exec_module._BUILDERS.copy()
    try:
        exec_module._BUILDERS = {}
        result = executor.select_workflow(intent="clinical_analysis", has_patient=True, is_critical=False)
        assert result is None
    finally:
        exec_module._BUILDERS = original


@pytest.mark.asyncio
async def test_execute_without_langgraph_returns_error(executor):
    import wanda.workflows.executor as exec_module
    original = exec_module._BUILDERS.copy()
    try:
        exec_module._BUILDERS = {}
        result = await executor.execute(
            workflow_name="clinical_analysis",
            query="test query",
            patient_id="p1",
            extra={},
        )
        assert isinstance(result, WorkflowResult)
        assert result.success is False
        assert result.error is not None
    finally:
        exec_module._BUILDERS = original


@pytest.mark.asyncio
async def test_execute_unknown_workflow(executor):
    import wanda.workflows.executor as exec_module
    original = exec_module._BUILDERS.copy()
    try:
        exec_module._BUILDERS = {"clinical_analysis": lambda: None}
        result = await executor.execute(
            workflow_name="nonexistent_workflow",
            query="test",
            patient_id=None,
            extra={},
        )
        assert result.success is False
        assert result.error is not None
    finally:
        exec_module._BUILDERS = original


@pytest.mark.asyncio
async def test_execute_returns_workflow_result_fields(executor):
    result = await executor.execute(
        workflow_name="clinical_analysis",
        query="paciente com CKD",
        patient_id="patient-001",
        extra={},
    )
    assert hasattr(result, "workflow_id")
    assert hasattr(result, "execution_id")
    assert hasattr(result, "latency_ms")
    assert hasattr(result, "key_points")
    assert isinstance(result.key_points, list)
    assert isinstance(result, WorkflowResult)


def test_workflow_result_defaults():
    r = WorkflowResult(
        workflow_id="wf-1",
        workflow_name="clinical_analysis",
        execution_id="exec-1",
        success=True,
    )
    assert r.synthesis is None
    assert r.key_points == []
    assert r.agent_responses == {}
    assert r.error is None
    assert r.latency_ms == 0
    assert r.iterations == 0


def test_workflow_result_error():
    r = WorkflowResult(
        workflow_id="wf-2",
        workflow_name="critical_alert",
        execution_id="exec-2",
        success=False,
        error="timeout exceeded",
    )
    assert not r.success
    assert r.error == "timeout exceeded"


def test_workflow_result_with_synthesis():
    r = WorkflowResult(
        workflow_id="wf-3",
        workflow_name="clinical_analysis",
        execution_id="exec-3",
        success=True,
        synthesis="Paciente com DM2 e HAS controlados.",
        key_points=["DM2 controlada", "HAS em alvo"],
        iterations=2,
        latency_ms=850,
    )
    assert r.synthesis == "Paciente com DM2 e HAS controlados."
    assert len(r.key_points) == 2
    assert r.iterations == 2


@pytest.mark.asyncio
async def test_workflow_executor_records_metrics_on_failure():
    import wanda.workflows.executor as exec_module

    metrics = MagicMock()
    executor = WorkflowExecutor(timeout_seconds=10, max_iterations=3, metrics_registry=metrics)
    original = exec_module._BUILDERS.copy()
    try:
        exec_module._BUILDERS = {}
        result = await executor.execute(
            workflow_name="clinical_analysis",
            query="teste",
            patient_id="p1",
            extra={},
        )
        assert result.success is False
        assert metrics.record_workflow_execution.called
    finally:
        exec_module._BUILDERS = original
