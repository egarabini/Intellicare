"""LangGraph node functions for WANDA workflows (EF-W005).

Each node function takes OrchestratorState and returns a partial update dict.
Nodes are pure async functions — no side effects beyond the state dict.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

import httpx

from wanda.workflows.state import AgentResponse, OrchestratorState

logger = logging.getLogger(__name__)


# ── IPS Loading ────────────────────────────────────────────────────


async def load_patient_ips(state: OrchestratorState) -> dict[str, Any]:
    """Load IPS from the IPS manager (injected via config closure).

    Graceful: if IPS unavailable, returns empty dict so workflow continues.
    """
    patient_id = state.get("patient_id")
    if not patient_id:
        logger.debug("No patient_id — skipping IPS load")
        return {"ips": None}

    # IPS manager is injected via closure when building the graph
    ips_loader = state.get("_ips_loader")  # type: ignore[misc]
    if ips_loader is None:
        return {"ips": None}

    try:
        ips = await ips_loader(patient_id)
        return {"ips": ips}
    except Exception as e:
        logger.warning("IPS load failed for %s: %s", patient_id, e)
        return {"ips": None}


# ── Agent Querying ─────────────────────────────────────────────────


async def _call_agent(
    base_url: str,
    endpoint: str,
    payload: dict[str, Any],
    timeout: float = 30.0,
) -> AgentResponse:
    """Call a single module endpoint and return structured result."""
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(base_url + endpoint, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return AgentResponse(success=True, data=data.get("data", data), latency_ms=0)
    except httpx.TimeoutException:
        return AgentResponse(success=False, data=None, error="timeout")
    except Exception as e:
        return AgentResponse(success=False, data=None, error=str(e))


async def query_florence(state: OrchestratorState) -> dict[str, Any]:
    """Query Florence (deep clinical analysis)."""
    responses = dict(state.get("agent_responses", {}))
    florence_url = state.get("_florence_url", "http://localhost:8002")  # type: ignore[misc]
    payload: dict[str, Any] = {"query": state.get("query", "")}
    if state.get("patient_id"):
        payload["patient_id"] = state["patient_id"]

    result = await _call_agent(florence_url, "/api/v1/analyze", payload)
    responses["intellicare-florence"] = result
    return {"agent_responses": responses}


async def query_oswaldo(state: OrchestratorState) -> dict[str, Any]:
    """Query Oswaldo (chronic disease engine)."""
    responses = dict(state.get("agent_responses", {}))
    oswaldo_url = state.get("_oswaldo_url", "http://localhost:8001")  # type: ignore[misc]
    patient_id = state.get("patient_id")

    if patient_id:
        result = await _call_agent(
            oswaldo_url,
            "/api/v1/analyze",
            {"patient_id": patient_id, "query": state.get("query", "")},
        )
    else:
        result = await _call_agent(oswaldo_url, "/api/v1/diseases", {})

    responses["intellicare-oswaldo"] = result
    return {"agent_responses": responses}


async def query_geralda(state: OrchestratorState) -> dict[str, Any]:
    """Query Geralda (patient accompaniment / care plans)."""
    responses = dict(state.get("agent_responses", {}))
    geralda_url = state.get("_geralda_url", "http://localhost:8006")  # type: ignore[misc]
    patient_id = state.get("patient_id")

    endpoint = f"/api/v1/plans" if patient_id else "/api/v1/education/conditions"
    payload: dict[str, Any] = {}
    if patient_id:
        payload["patient_id"] = patient_id

    result = await _call_agent(geralda_url, endpoint, payload)
    responses["intellicare-geralda"] = result
    return {"agent_responses": responses}


async def query_zilda(state: OrchestratorState) -> dict[str, Any]:
    """Query Zilda (Brazilian health data / CNES / DATASUS)."""
    responses = dict(state.get("agent_responses", {}))
    zilda_url = state.get("_zilda_url", "http://localhost:8003")  # type: ignore[misc]
    result = await _call_agent(zilda_url, "/api/v1/regions", {})
    responses["intellicare-zilda"] = result
    return {"agent_responses": responses}


async def query_agents_parallel(state: OrchestratorState) -> dict[str, Any]:
    """Run Florence + Oswaldo + Geralda in parallel (clinical analysis workflow)."""
    tasks = [
        query_florence(state),
        query_oswaldo(state),
        query_geralda(state),
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    responses = dict(state.get("agent_responses", {}))
    agent_names = ["intellicare-florence", "intellicare-oswaldo", "intellicare-geralda"]

    for name, result in zip(agent_names, results):
        if isinstance(result, Exception):
            responses[name] = AgentResponse(success=False, data=None, error=str(result))
        elif isinstance(result, dict) and "agent_responses" in result:
            responses.update(result["agent_responses"])

    return {"agent_responses": responses}


# ── Completeness Check ─────────────────────────────────────────────


async def llm_check_completeness(state: OrchestratorState) -> dict[str, Any]:
    """Use LLM to assess if responses are complete or if more data is needed.

    Returns next_step = "aggregate" (done) or "get_more_data" (needs refinement).
    Graceful: if LLM unavailable, skips to aggregation.
    """
    iterations = state.get("iterations", 0)
    max_iterations = state.get("max_iterations", 3)

    if iterations >= max_iterations:
        logger.info("Max iterations (%d) reached — proceeding to aggregation", max_iterations)
        return {"next_step": "aggregate", "iterations": iterations}

    llm_provider = state.get("_llm_provider")  # type: ignore[misc]
    if llm_provider is None:
        return {"next_step": "aggregate", "iterations": iterations}

    responses = state.get("agent_responses", {})
    successful = {k: v for k, v in responses.items() if v.get("success")}

    if not successful:
        return {"next_step": "aggregate", "iterations": iterations}

    try:
        responses_summary = json.dumps(
            {k: str(v.get("data", ""))[:500] for k, v in successful.items()},
            ensure_ascii=False,
        )
        system_prompt = (
            "Voce avalia se as respostas dos agentes sao suficientes para responder a consulta. "
            "Retorne JSON: {\"complete\": true/false, \"reason\": \"...\"}"
        )
        user_msg = f"Consulta: {state.get('query', '')}\n\nRespostas: {responses_summary}"

        llm_response = await llm_provider.chat(
            system_prompt=system_prompt,
            user_message=user_msg,
        )
        data = json.loads(llm_response.content)
        complete = bool(data.get("complete", True))
        next_step = "aggregate" if complete else "get_more_data"
        return {"next_step": next_step, "iterations": iterations + 1}
    except Exception as e:
        logger.warning("LLM completeness check failed: %s — proceeding to aggregation", e)
        return {"next_step": "aggregate", "iterations": iterations}


# ── Aggregation ────────────────────────────────────────────────────


async def final_aggregation(state: OrchestratorState) -> dict[str, Any]:
    """Synthesize all agent responses into a final answer.

    Uses the IntelligentAggregator if available, otherwise builds a simple summary.
    """
    responses = state.get("agent_responses", {})
    successful = {k: v for k, v in responses.items() if v.get("success")}

    if not successful:
        return {"synthesis": "Nenhum agente retornou dados.", "key_points": []}

    parts = []
    for agent, resp in successful.items():
        data = resp.get("data")
        if data:
            parts.append(f"[{agent}]: {str(data)[:1000]}")

    synthesis = "\n\n".join(parts)
    key_points = [f"Dados de {agent}" for agent in successful.keys()]

    return {"synthesis": synthesis, "key_points": key_points}


# ── Onboarding-specific ────────────────────────────────────────────


async def query_agents_onboarding(state: OrchestratorState) -> dict[str, Any]:
    """Florence (histórico) + Zilda (UBS referência) + Geralda (jornada) in parallel."""
    tasks = [
        query_florence(state),
        query_zilda(state),
        query_geralda(state),
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    responses = dict(state.get("agent_responses", {}))
    agent_names = ["intellicare-florence", "intellicare-zilda", "intellicare-geralda"]

    for name, result in zip(agent_names, results):
        if isinstance(result, Exception):
            responses[name] = AgentResponse(success=False, data=None, error=str(result))
        elif isinstance(result, dict) and "agent_responses" in result:
            responses.update(result["agent_responses"])

    return {"agent_responses": responses}


# ── Critical Alert ─────────────────────────────────────────────────


async def query_agents_critical(state: OrchestratorState) -> dict[str, Any]:
    """Florence (analysis) + Oswaldo (context) + Geralda (status) in parallel."""
    tasks = [
        query_florence(state),
        query_oswaldo(state),
        query_geralda(state),
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    responses = dict(state.get("agent_responses", {}))
    agent_names = ["intellicare-florence", "intellicare-oswaldo", "intellicare-geralda"]

    for name, result in zip(agent_names, results):
        if isinstance(result, Exception):
            responses[name] = AgentResponse(success=False, data=None, error=str(result))
        elif isinstance(result, dict) and "agent_responses" in result:
            responses.update(result["agent_responses"])

    return {"agent_responses": responses, "next_step": "check_severity"}


async def check_severity_and_escalate(state: OrchestratorState) -> dict[str, Any]:
    """Determine severity and flag for escalation if critical."""
    responses = state.get("agent_responses", {})
    has_critical = any(
        "critic" in str(v.get("data", "")).lower()
        or "urgente" in str(v.get("data", "")).lower()
        for v in responses.values()
        if v.get("success")
    )
    next_step = "escalate" if has_critical else "aggregate"
    return {"next_step": next_step}
