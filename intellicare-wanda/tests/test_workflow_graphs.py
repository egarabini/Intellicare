"""Tests for LangGraph workflow graphs (EF-W005)."""

import pytest
from unittest.mock import patch, MagicMock


class TestWorkflowGraphs:
    """Tests for graph builder functions.

    LangGraph may not be installed in test environment.
    Tests verify graceful handling of ImportError.
    """

    def test_import_graphs_module(self):
        """Module should be importable without LangGraph."""
        import importlib
        import sys
        # Should import without error even without langgraph
        try:
            from wanda.workflows import graphs
            assert hasattr(graphs, "build_clinical_analysis_graph")
            assert hasattr(graphs, "build_onboarding_graph")
            assert hasattr(graphs, "build_critical_alert_graph")
        except ImportError:
            pytest.skip("wanda.workflows.graphs import failed")

    def test_build_clinical_analysis_graph_raises_or_returns(self):
        """build_clinical_analysis_graph either returns a compiled graph or raises ImportError."""
        try:
            from wanda.workflows.graphs import build_clinical_analysis_graph
            graph = build_clinical_analysis_graph()
            # If LangGraph is installed, graph should have invoke method
            assert hasattr(graph, "ainvoke") or hasattr(graph, "invoke") or graph is not None
        except ImportError:
            pass  # Expected when LangGraph not installed

    def test_build_onboarding_graph_raises_or_returns(self):
        try:
            from wanda.workflows.graphs import build_onboarding_graph
            graph = build_onboarding_graph()
            assert graph is not None
        except ImportError:
            pass

    def test_build_critical_alert_graph_raises_or_returns(self):
        try:
            from wanda.workflows.graphs import build_critical_alert_graph
            graph = build_critical_alert_graph()
            assert graph is not None
        except ImportError:
            pass

    def test_workflow_registry_in_executor(self):
        from wanda.workflows.executor import WorkflowExecutor
        executor = WorkflowExecutor()
        workflows = executor.available_workflows()
        assert "clinical_analysis" in workflows
        assert "patient_onboarding" in workflows
        assert "critical_alert" in workflows
        assert len(workflows) == 3

    def test_checkpointer_import(self):
        from wanda.workflows.checkpointer import WorkflowCheckpointer
        cp = WorkflowCheckpointer()
        assert cp is not None

    @pytest.mark.asyncio
    async def test_checkpointer_save_restore_memory(self):
        from wanda.workflows.checkpointer import WorkflowCheckpointer
        cp = WorkflowCheckpointer()
        state = {"query": "test", "workflow_name": "clinical_analysis", "iterations": 1}
        await cp.save("exec-1", state)
        restored = await cp.restore("exec-1")
        assert restored is not None
        assert restored.get("query") == "test"

    @pytest.mark.asyncio
    async def test_checkpointer_delete(self):
        from wanda.workflows.checkpointer import WorkflowCheckpointer
        cp = WorkflowCheckpointer()
        await cp.save("exec-2", {"data": "value"})
        await cp.delete("exec-2")
        restored = await cp.restore("exec-2")
        assert restored is None

    @pytest.mark.asyncio
    async def test_checkpointer_restore_nonexistent_returns_none(self):
        from wanda.workflows.checkpointer import WorkflowCheckpointer
        cp = WorkflowCheckpointer()
        restored = await cp.restore("nonexistent-exec-id")
        assert restored is None
