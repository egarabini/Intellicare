"""WorkflowExecutor — runs LangGraph workflows with timeout and fallback (EF-W005)."""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from wanda.workflows.checkpointer import WorkflowCheckpointer
from wanda.workflows.state import OrchestratorState

logger = logging.getLogger(__name__)


@dataclass
class WorkflowResult:
    """Result returned after a workflow execution."""

    workflow_id: str
    workflow_name: str
    execution_id: str
    success: bool
    synthesis: Optional[str] = None
    key_points: list[str] = field(default_factory=list)
    agent_responses: dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    latency_ms: int = 0
    iterations: int = 0


# ── Workflow Registry ──────────────────────────────────────────────

# Lazy-loaded builders — avoids importing langgraph at module level
# so the module loads even if langgraph is not installed.
_BUILDERS: dict[str, Callable[[], Any]] = {}


def _register_workflows() -> None:
    """Register available workflows (called once on first use)."""
    global _BUILDERS
    if _BUILDERS:
        return
    try:
        from wanda.workflows.graphs import (
            build_clinical_analysis_graph,
            build_onboarding_graph,
            build_critical_alert_graph,
        )
        _BUILDERS = {
            "clinical_analysis": build_clinical_analysis_graph,
            "patient_onboarding": build_onboarding_graph,
            "critical_alert": build_critical_alert_graph,
        }
        logger.info("LangGraph workflows registered: %s", list(_BUILDERS.keys()))
    except ImportError as e:
        logger.warning("LangGraph not available: %s — workflows disabled", e)


class WorkflowExecutor:
    """Executes LangGraph workflows with timeout control and Redis checkpointing.

    Usage:
        executor = WorkflowExecutor(config, redis_client, ips_manager)
        result = await executor.execute("clinical_analysis", initial_state)
    """

    def __init__(
        self,
        timeout_seconds: int = 60,
        max_iterations: int = 3,
        redis_client: Any = None,
        llm_provider: Any = None,
        module_urls: Optional[dict[str, str]] = None,
        metrics_registry: Any = None,
    ) -> None:
        self._timeout = timeout_seconds
        self._max_iterations = max_iterations
        self._checkpointer = WorkflowCheckpointer(redis_client=redis_client)
        self._llm_provider = llm_provider
        self._module_urls = module_urls or {}
        self._metrics = metrics_registry
        self._compiled_graphs: dict[str, Any] = {}

        _register_workflows()

    def available_workflows(self) -> list[str]:
        """Return names of all registered workflows."""
        return list(_BUILDERS.keys())

    def _get_or_compile(self, workflow_name: str) -> Any:
        """Get compiled graph, building it on first access."""
        if workflow_name not in self._compiled_graphs:
            builder = _BUILDERS.get(workflow_name)
            if builder is None:
                raise ValueError(f"Unknown workflow: {workflow_name!r}")
            self._compiled_graphs[workflow_name] = builder()
        return self._compiled_graphs[workflow_name]

    def _build_initial_state(
        self,
        workflow_name: str,
        execution_id: str,
        query: str,
        tenant_id: str = "default",
        patient_id: Optional[str] = None,
        extra: Optional[dict[str, Any]] = None,
    ) -> OrchestratorState:
        """Build the initial state dict injecting config and callables."""
        state: OrchestratorState = {
            "query": query,
            "tenant_id": tenant_id,
            "patient_id": patient_id,
            "workflow_id": execution_id,
            "workflow_name": workflow_name,
            "agent_responses": {},
            "synthesis": None,
            "key_points": [],
            "next_step": "continue",
            "iterations": 0,
            "max_iterations": self._max_iterations,
            "error": None,
            # Injected callables (stripped before checkpointing)
            "_llm_provider": self._llm_provider,  # type: ignore[typeddict-item]
            "_florence_url": self._module_urls.get("intellicare-florence", "http://localhost:8002"),  # type: ignore[typeddict-item]
            "_oswaldo_url": self._module_urls.get("intellicare-oswaldo", "http://localhost:8001"),  # type: ignore[typeddict-item]
            "_geralda_url": self._module_urls.get("intellicare-geralda", "http://localhost:8006"),  # type: ignore[typeddict-item]
            "_zilda_url": self._module_urls.get("intellicare-zilda", "http://localhost:8003"),  # type: ignore[typeddict-item]
        }
        if extra:
            state.update(extra)  # type: ignore[typeddict-item]
        return state

    async def execute(
        self,
        workflow_name: str,
        query: str,
        tenant_id: str = "default",
        patient_id: Optional[str] = None,
        extra: Optional[dict[str, Any]] = None,
    ) -> WorkflowResult:
        """Execute a named workflow with timeout.

        Returns WorkflowResult — never raises (errors captured in result.error).
        """
        execution_id = str(uuid.uuid4())
        t_start = time.monotonic()

        if not _BUILDERS:
            result = WorkflowResult(
                workflow_id=execution_id,
                workflow_name=workflow_name,
                execution_id=execution_id,
                success=False,
                error="LangGraph not available",
            )
            self._record_metrics(result)
            return result

        try:
            graph = self._get_or_compile(workflow_name)
        except (ValueError, ImportError) as e:
            result = WorkflowResult(
                workflow_id=execution_id,
                workflow_name=workflow_name,
                execution_id=execution_id,
                success=False,
                error=str(e),
            )
            self._record_metrics(result)
            return result

        initial_state = self._build_initial_state(
            workflow_name, execution_id, query, tenant_id, patient_id, extra
        )

        try:
            final_state: OrchestratorState = await asyncio.wait_for(
                graph.ainvoke(initial_state),
                timeout=self._timeout,
            )
        except asyncio.TimeoutError:
            logger.warning("Workflow %s timed out after %ds", workflow_name, self._timeout)
            result = WorkflowResult(
                workflow_id=execution_id,
                workflow_name=workflow_name,
                execution_id=execution_id,
                success=False,
                error=f"Workflow timeout after {self._timeout}s",
                latency_ms=int((time.monotonic() - t_start) * 1000),
            )
            self._record_metrics(result)
            return result
        except Exception as e:
            logger.exception("Workflow %s failed: %s", workflow_name, e)
            result = WorkflowResult(
                workflow_id=execution_id,
                workflow_name=workflow_name,
                execution_id=execution_id,
                success=False,
                error=str(e),
                latency_ms=int((time.monotonic() - t_start) * 1000),
            )
            self._record_metrics(result)
            return result

        # Checkpoint final state
        await self._checkpointer.save(tenant_id, execution_id, dict(final_state))

        latency_ms = int((time.monotonic() - t_start) * 1000)
        result = WorkflowResult(
            workflow_id=execution_id,
            workflow_name=workflow_name,
            execution_id=execution_id,
            success=True,
            synthesis=final_state.get("synthesis"),
            key_points=final_state.get("key_points", []),
            agent_responses=final_state.get("agent_responses", {}),
            error=final_state.get("error"),
            latency_ms=latency_ms,
            iterations=final_state.get("iterations", 0),
        )
        self._record_metrics(result)
        return result

    def select_workflow(
        self,
        intent: str,
        has_patient: bool = False,
        is_critical: bool = False,
    ) -> Optional[str]:
        """Select the best workflow for the given intent.

        Returns workflow name or None if no suitable workflow found.
        """
        if not _BUILDERS:
            return None

        if is_critical:
            return "critical_alert"

        intent_lower = intent.lower()
        if "onboarding" in intent_lower or "internacao" in intent_lower or "admissao" in intent_lower:
            return "patient_onboarding"
        if has_patient and any(
            kw in intent_lower
            for kw in ["analise", "avaliacao", "completa", "completo", "resumo"]
        ):
            return "clinical_analysis"

        return None

    def set_metrics_registry(self, metrics_registry: Any) -> None:
        self._metrics = metrics_registry

    def _record_metrics(self, result: WorkflowResult) -> None:
        if self._metrics is None:
            return
        try:
            self._metrics.record_workflow_execution(
                workflow_id=result.workflow_name,
                status="success" if result.success else "failed",
                duration_seconds=max(0.0, float(result.latency_ms) / 1000.0),
                iterations=result.iterations,
            )
        except Exception:
            return
