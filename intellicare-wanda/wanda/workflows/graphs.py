"""LangGraph StateGraph builders for WANDA workflows (EF-W005).

Three workflows:
1. clinical_analysis  — Florence + Oswaldo + Geralda parallel → LLM completeness check → aggregate
2. patient_onboarding — Florence + Zilda + Geralda parallel → aggregate
3. critical_alert     — Florence + Oswaldo + Geralda parallel → severity check → [escalate|aggregate]

LangGraph is imported lazily so the module still loads if langgraph is not installed.
"""

from __future__ import annotations

import logging
from typing import Any

from wanda.workflows.state import OrchestratorState

logger = logging.getLogger(__name__)


def _check_completeness(state: OrchestratorState) -> str:
    """Conditional edge: returns next node name based on state.next_step."""
    return state.get("next_step", "aggregate")


def _check_severity(state: OrchestratorState) -> str:
    """Conditional edge for critical_alert: escalate or aggregate."""
    return state.get("next_step", "aggregate")


def build_clinical_analysis_graph() -> Any:
    """Build the clinical analysis workflow graph.

    Flow: load_ips → query_agents_parallel → llm_check_completeness
          → [if complete] final_aggregation
          → [if needs more] query_agents_parallel (up to max_iterations)

    Returns:
        Compiled LangGraph StateGraph.

    Raises:
        ImportError: If langgraph is not installed.
    """
    from langgraph.graph import StateGraph, END  # type: ignore[import]
    from wanda.workflows.nodes import (
        load_patient_ips,
        query_agents_parallel,
        llm_check_completeness,
        final_aggregation,
    )

    graph = StateGraph(OrchestratorState)

    graph.add_node("load_ips", load_patient_ips)
    graph.add_node("query_agents", query_agents_parallel)
    graph.add_node("check_completeness", llm_check_completeness)
    graph.add_node("aggregate", final_aggregation)

    graph.set_entry_point("load_ips")
    graph.add_edge("load_ips", "query_agents")
    graph.add_edge("query_agents", "check_completeness")
    graph.add_conditional_edges(
        "check_completeness",
        _check_completeness,
        {
            "aggregate": "aggregate",
            "get_more_data": "query_agents",  # refinement loop
        },
    )
    graph.add_edge("aggregate", END)

    return graph.compile()


def build_onboarding_graph() -> Any:
    """Build the patient onboarding workflow graph.

    Flow: load_ips → query_agents_onboarding → final_aggregation

    Returns:
        Compiled LangGraph StateGraph.
    """
    from langgraph.graph import StateGraph, END  # type: ignore[import]
    from wanda.workflows.nodes import (
        load_patient_ips,
        query_agents_onboarding,
        final_aggregation,
    )

    graph = StateGraph(OrchestratorState)

    graph.add_node("load_ips", load_patient_ips)
    graph.add_node("query_agents", query_agents_onboarding)
    graph.add_node("aggregate", final_aggregation)

    graph.set_entry_point("load_ips")
    graph.add_edge("load_ips", "query_agents")
    graph.add_edge("query_agents", "aggregate")
    graph.add_edge("aggregate", END)

    return graph.compile()


def build_critical_alert_graph() -> Any:
    """Build the critical alert multi-agent workflow graph.

    Flow: load_ips → query_agents_critical → check_severity
          → [escalate] → aggregate
          → [normal]   → aggregate

    Returns:
        Compiled LangGraph StateGraph.
    """
    from langgraph.graph import StateGraph, END  # type: ignore[import]
    from wanda.workflows.nodes import (
        load_patient_ips,
        query_agents_critical,
        check_severity_and_escalate,
        final_aggregation,
    )

    async def escalate_and_aggregate(state: OrchestratorState) -> dict[str, Any]:
        """Mark as critical escalation then aggregate."""
        responses = state.get("agent_responses", {})
        logger.warning(
            "CRITICAL escalation triggered for patient %s — %d agents responded",
            state.get("patient_id", "unknown"),
            len(responses),
        )
        result = await final_aggregation(state)
        return {**result, "next_step": "escalated"}

    graph = StateGraph(OrchestratorState)

    graph.add_node("load_ips", load_patient_ips)
    graph.add_node("query_agents", query_agents_critical)
    graph.add_node("check_severity", check_severity_and_escalate)
    graph.add_node("escalate", escalate_and_aggregate)
    graph.add_node("aggregate", final_aggregation)

    graph.set_entry_point("load_ips")
    graph.add_edge("load_ips", "query_agents")
    graph.add_edge("query_agents", "check_severity")
    graph.add_conditional_edges(
        "check_severity",
        _check_severity,
        {
            "escalate": "escalate",
            "aggregate": "aggregate",
        },
    )
    graph.add_edge("escalate", END)
    graph.add_edge("aggregate", END)

    return graph.compile()
