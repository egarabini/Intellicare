"""Rastreabilidade de decisoes da Wanda."""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta


@dataclass
class AgentCallTrace:
    agent_name: str
    endpoint: str
    status_code: int
    latency_ms: int
    success: bool
    error: str | None = None
    request_payload_hash: str = ""


@dataclass
class DecisionTrace:
    trace_id: str
    original_query: str
    patient_id: str | None
    routing_method: str
    success: bool
    total_latency_ms: int
    created_at: datetime = field(default_factory=datetime.utcnow)
    routing_reasoning: str | None = None
    agent_calls: list[AgentCallTrace] = field(default_factory=list)


@dataclass
class TraceContext:
    trace_id: str
    started_at: datetime
    original_query: str
    patient_id: str | None
    routing_method: str | None = None
    routing_reasoning: str | None = None
    agent_calls: list[AgentCallTrace] = field(default_factory=list)


class InMemoryTraceStore:
    def __init__(self) -> None:
        self._traces: dict[str, DecisionTrace] = {}

    async def save(self, trace: DecisionTrace) -> None:
        self._traces[trace.trace_id] = trace

    async def get(self, trace_id: str) -> DecisionTrace | None:
        return self._traces.get(trace_id)

    async def search(
        self,
        patient_id: str | None = None,
        success: bool | None = None,
        agent: str | None = None,
        limit: int = 100,
    ) -> list[DecisionTrace]:
        traces = list(self._traces.values())
        if patient_id is not None:
            traces = [trace for trace in traces if trace.patient_id == patient_id]
        if success is not None:
            traces = [trace for trace in traces if trace.success == success]
        if agent is not None:
            traces = [trace for trace in traces if any(call.agent_name == agent for call in trace.agent_calls)]
        traces.sort(key=lambda item: item.created_at, reverse=True)
        return traces[: max(1, min(limit, 200))]


class TraceQueryService:
    """Consultas e analise agregada de traces em memoria."""

    def __init__(self, store: InMemoryTraceStore) -> None:
        self._store = store

    async def analyze_routing_patterns(self, period_days: int = 30) -> dict[str, object]:
        traces = await self._store.search(limit=500)
        cutoff = datetime.utcnow() - timedelta(days=max(1, period_days))
        traces = [trace for trace in traces if trace.created_at >= cutoff]
        method_counts: dict[str, int] = {}
        agent_counts: dict[str, int] = {}
        total = 0
        failed = 0
        for trace in traces:
            total += 1
            if not trace.success:
                failed += 1
            method_counts[trace.routing_method] = method_counts.get(trace.routing_method, 0) + 1
            for call in trace.agent_calls:
                agent_counts[call.agent_name] = agent_counts.get(call.agent_name, 0) + 1
        top_agents = sorted(agent_counts.items(), key=lambda item: item[1], reverse=True)[:5]
        return {
            "period_days": period_days,
            "total_traces": total,
            "failed_traces": failed,
            "routing_methods": method_counts,
            "top_agents": [{"agent": name, "count": count} for name, count in top_agents],
        }

    async def find_anomalies(self, period_days: int = 7) -> list[dict[str, object]]:
        traces = await self._store.search(limit=500)
        cutoff = datetime.utcnow() - timedelta(days=max(1, period_days))
        traces = [trace for trace in traces if trace.created_at >= cutoff]
        anomalies: list[dict[str, object]] = []
        if not traces:
            return anomalies
        failed = [trace for trace in traces if not trace.success]
        failure_rate = len(failed) / len(traces)
        if failure_rate >= 0.4:
            anomalies.append(
                {
                    "type": "high_failure_rate",
                    "severity": "high",
                    "value": round(failure_rate, 3),
                    "description": "Taxa de falha acima de 40% no periodo analisado.",
                }
            )

        ordered = sorted(traces, key=lambda item: item.created_at)
        if len(ordered) >= 10:
            pivot = len(ordered) // 2
            baseline = ordered[:pivot]
            recent = ordered[pivot:]
            base_p95 = self._p95([trace.total_latency_ms for trace in baseline])
            recent_p95 = self._p95([trace.total_latency_ms for trace in recent])
            if base_p95 and recent_p95 and recent_p95 > (base_p95 * 1.5) and recent_p95 > 5000:
                anomalies.append(
                    {
                        "type": "latency_regression",
                        "severity": "high",
                        "baseline_p95_ms": int(base_p95),
                        "recent_p95_ms": int(recent_p95),
                        "description": "P95 de latencia aumentou significativamente no periodo recente.",
                    }
                )

        agent_totals: dict[str, int] = {}
        agent_failures: dict[str, int] = {}
        for trace in traces:
            for call in trace.agent_calls:
                agent_totals[call.agent_name] = agent_totals.get(call.agent_name, 0) + 1
                if not call.success:
                    agent_failures[call.agent_name] = agent_failures.get(call.agent_name, 0) + 1
        for agent_name, total in agent_totals.items():
            if total < 3:
                continue
            rate = agent_failures.get(agent_name, 0) / total
            if rate >= 0.5:
                anomalies.append(
                    {
                        "type": "agent_error_spike",
                        "severity": "warning",
                        "agent": agent_name,
                        "error_rate": round(rate, 3),
                        "calls": total,
                        "description": "Taxa de erro elevada para agente no periodo analisado.",
                    }
                )

        for trace in traces:
            if trace.total_latency_ms > 5000:
                anomalies.append(
                    {
                        "type": "high_latency_trace",
                        "severity": "warning",
                        "trace_id": trace.trace_id,
                        "latency_ms": trace.total_latency_ms,
                        "description": "Trace acima de 5s.",
                    }
                )
        return anomalies

    @staticmethod
    def _p95(values: list[int]) -> float | None:
        if not values:
            return None
        ordered = sorted(values)
        index = max(0, int(round(0.95 * (len(ordered) - 1))))
        return float(ordered[index])


class FHIRAuditExporter:
    """Exportador basico de DecisionTrace para FHIR AuditEvent."""

    async def export_decision(self, trace: DecisionTrace) -> dict:
        outcome = "0" if trace.success else "4"
        return {
            "resourceType": "AuditEvent",
            "type": {"system": "intellicare", "code": "orchestration"},
            "action": "E",
            "outcome": outcome,
            "recorded": trace.created_at.isoformat(),
            "agent": [{"requestor": True, "name": "wanda"}],
            "source": {"site": "intellicare-wanda"},
            "entity": [
                {
                    "role": {"code": "query"},
                    "detail": [{"type": "query", "valueString": trace.original_query[:200]}],
                },
                {
                    "role": {"code": "routing"},
                    "detail": [{"type": "routing_method", "valueString": trace.routing_method}],
                },
            ],
        }


class DecisionTracer:
    def __init__(self, store: InMemoryTraceStore) -> None:
        self._store = store

    async def start_trace(self, query: str, patient_id: str | None) -> TraceContext:
        return TraceContext(
            trace_id=str(uuid.uuid4()),
            started_at=datetime.utcnow(),
            original_query=query,
            patient_id=patient_id,
        )

    async def record_routing(self, context: TraceContext, routing_method: str, reasoning: str | None = None) -> None:
        context.routing_method = routing_method
        context.routing_reasoning = reasoning

    async def record_agent_call(
        self,
        context: TraceContext,
        agent_name: str,
        endpoint: str,
        payload: dict | None,
        status_code: int,
        latency_ms: int,
        success: bool,
        error: str | None = None,
    ) -> None:
        payload_hash = hashlib.sha256(str(payload or {}).encode("utf-8")).hexdigest()
        context.agent_calls.append(
            AgentCallTrace(
                agent_name=agent_name,
                endpoint=endpoint,
                status_code=status_code,
                latency_ms=latency_ms,
                success=success,
                error=error,
                request_payload_hash=payload_hash,
            )
        )

    async def complete_trace(self, context: TraceContext, success: bool) -> DecisionTrace:
        elapsed_ms = int((datetime.utcnow() - context.started_at).total_seconds() * 1000)
        trace = DecisionTrace(
            trace_id=context.trace_id,
            original_query=context.original_query,
            patient_id=context.patient_id,
            routing_method=context.routing_method or "unknown",
            routing_reasoning=context.routing_reasoning,
            success=success,
            total_latency_ms=max(0, elapsed_ms),
            agent_calls=context.agent_calls,
        )
        await self._store.save(trace)
        return trace
