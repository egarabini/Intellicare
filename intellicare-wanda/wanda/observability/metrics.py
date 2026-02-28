"""Metricas Prometheus para Wanda."""

from __future__ import annotations

from datetime import datetime
from math import ceil

from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram, generate_latest

from wanda.observability.slo_store import InMemorySLOHistoryStore


class MetricsRegistry:
    def __init__(
        self,
        registry: CollectorRegistry | None = None,
        history_store=None,
        history_limit: int = 200,
    ) -> None:
        self.registry = registry or CollectorRegistry(auto_describe=True)
        self._history_limit = max(10, int(history_limit))
        self._history_store = history_store or InMemorySLOHistoryStore(max_items=self._history_limit)
        self._slo_history: list[dict[str, object]] = self._history_store.list(limit=self._history_limit)
        self._latency_seconds: list[float] = []
        self._max_latency_window = 5000
        self._orchestration_total = 0
        self._orchestration_success = 0
        self._agent_total = 0
        self._agent_success = 0
        self._agent_stats: dict[str, dict[str, float]] = {}
        self._routing_stats: dict[str, int] = {"llm": 0, "keyword": 0, "other": 0}
        self._routing_confidences: list[float] = []
        self._ips_hits = 0
        self._ips_misses = 0
        self._ips_age_hours: list[float] = []
        self._alert_ack_seconds: dict[str, list[float]] = {}
        self._alerts_pending_state: dict[str, float] = {}
        self.orchestration_requests_total = Counter(
            "wanda_orchestration_requests_total",
            "Total de requisicoes de orquestracao",
            ["request_type", "routing_method", "status"],
            registry=self.registry,
        )
        self.orchestration_duration_seconds = Histogram(
            "wanda_orchestration_duration_seconds",
            "Duracao total da orquestracao",
            ["request_type", "routing_method"],
            registry=self.registry,
        )
        self.orchestration_in_flight = Gauge(
            "wanda_orchestration_in_flight",
            "Orquestracoes em andamento",
            registry=self.registry,
        )
        self.agent_calls_total = Counter(
            "wanda_agent_calls_total",
            "Total de chamadas a agentes",
            ["agent", "capability", "status"],
            registry=self.registry,
        )
        self.agent_response_duration = Histogram(
            "wanda_agent_response_duration_seconds",
            "Latencia de resposta dos agentes",
            ["agent", "capability"],
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 15.0, 30.0],
            registry=self.registry,
        )
        self.agent_error_rate = Gauge(
            "wanda_agent_error_rate",
            "Taxa de erros por agente (aproximacao runtime)",
            ["agent"],
            registry=self.registry,
        )
        self.circuit_breaker_state = Gauge(
            "wanda_circuit_breaker_state",
            "Estado do circuit breaker",
            ["agent"],
            registry=self.registry,
        )
        self.circuit_breaker_transitions_total = Counter(
            "wanda_circuit_breaker_transitions_total",
            "Transicoes do circuit breaker",
            ["agent", "from_state", "to_state"],
            registry=self.registry,
        )
        self.routing_decisions_total = Counter(
            "wanda_routing_decisions_total",
            "Decisoes de roteamento",
            ["method", "agents_count", "success"],
            registry=self.registry,
        )
        self.routing_llm_confidence = Histogram(
            "wanda_routing_llm_confidence",
            "Confianca do LLM no roteamento",
            buckets=[0.1, 0.3, 0.5, 0.7, 0.8, 0.9, 0.95, 1.0],
            registry=self.registry,
        )
        self.routing_fallback_total = Counter(
            "wanda_routing_fallback_total",
            "Fallbacks de LLM para keyword",
            ["reason"],
            registry=self.registry,
        )
        self.ips_cache_hit_total = Counter(
            "wanda_ips_cache_hit_total",
            "Cache hits do IPS",
            ["freshness"],
            registry=self.registry,
        )
        self.ips_cache_miss_total = Counter(
            "wanda_ips_cache_miss_total",
            "Cache misses do IPS",
            ["reason"],
            registry=self.registry,
        )
        self.ips_load_duration_seconds = Histogram(
            "wanda_ips_load_duration_seconds",
            "Tempo de carregamento do IPS",
            registry=self.registry,
        )
        self.ips_age_hours = Histogram(
            "wanda_ips_age_hours",
            "Idade do IPS utilizado em horas",
            buckets=[0.1, 0.5, 1.0, 4.0, 12.0, 24.0, 72.0],
            registry=self.registry,
        )
        self.alerts_received_total = Counter(
            "wanda_alerts_received_total",
            "Total de alertas recebidos",
            ["source_agent", "severity"],
            registry=self.registry,
        )
        self.alerts_pending = Gauge(
            "wanda_alerts_pending",
            "Alertas pendentes",
            ["severity"],
            registry=self.registry,
        )
        self.alert_acknowledgment_seconds = Histogram(
            "wanda_alert_acknowledgment_seconds",
            "Tempo para reconhecimento de alerta",
            ["severity"],
            registry=self.registry,
        )
        self.alerts_escalated_total = Counter(
            "wanda_alerts_escalated_total",
            "Alertas escalados por nao reconhecimento",
            ["severity"],
            registry=self.registry,
        )
        self.workflow_executions_total = Counter(
            "wanda_workflow_executions_total",
            "Execucoes de workflows",
            ["workflow_id", "status"],
            registry=self.registry,
        )
        self.workflow_duration_seconds = Histogram(
            "wanda_workflow_duration_seconds",
            "Duracao dos workflows",
            ["workflow_id"],
            registry=self.registry,
        )
        self.workflow_iterations = Histogram(
            "wanda_workflow_iterations",
            "Iteracoes por workflow",
            ["workflow_id"],
            buckets=[1, 2, 3, 5, 10],
            registry=self.registry,
        )

    def render(self) -> bytes:
        return generate_latest(self.registry)

    def record_orchestration(self, request_type: str, routing_method: str, status: str, elapsed_seconds: float) -> None:
        elapsed = max(0.0, float(elapsed_seconds))
        self.orchestration_requests_total.labels(request_type, routing_method, status).inc()
        self.orchestration_duration_seconds.labels(request_type, routing_method).observe(elapsed)
        self._orchestration_total += 1
        if status == "success":
            self._orchestration_success += 1
        self._latency_seconds.append(elapsed)
        if len(self._latency_seconds) > self._max_latency_window:
            self._latency_seconds = self._latency_seconds[-self._max_latency_window :]

    def record_agent_call(self, agent: str, capability: str, status: str, latency_seconds: float | None = None) -> None:
        self.agent_calls_total.labels(agent, capability, status).inc()
        self._agent_total += 1
        if status == "success":
            self._agent_success += 1
        stats = self._agent_stats.setdefault(agent, {"total": 0.0, "success": 0.0, "latency_sum": 0.0, "latency_count": 0.0})
        stats["total"] += 1
        if status == "success":
            stats["success"] += 1
        if latency_seconds is not None:
            latency = max(0.0, float(latency_seconds))
            stats["latency_sum"] += latency
            stats["latency_count"] += 1
            self.agent_response_duration.labels(agent, capability).observe(latency)
        error_rate = 1.0 - ((stats["success"] / stats["total"]) if stats["total"] > 0 else 1.0)
        self.agent_error_rate.labels(agent).set(max(0.0, min(1.0, error_rate)))

    def record_routing_decision(
        self,
        method: str,
        agents_count: int,
        success: bool,
        llm_confidence: float | None = None,
        fallback_reason: str | None = None,
    ) -> None:
        self.routing_decisions_total.labels(method, str(max(0, agents_count)), str(bool(success)).lower()).inc()
        method_key = method if method in ("llm", "keyword") else "other"
        self._routing_stats[method_key] = self._routing_stats.get(method_key, 0) + 1
        if llm_confidence is not None:
            confidence = max(0.0, min(1.0, float(llm_confidence)))
            self.routing_llm_confidence.observe(confidence)
            self._routing_confidences.append(confidence)
            if len(self._routing_confidences) > self._max_latency_window:
                self._routing_confidences = self._routing_confidences[-self._max_latency_window :]
        if fallback_reason:
            self.routing_fallback_total.labels(fallback_reason).inc()

    def record_circuit_transition(self, agent: str, from_state: str, to_state: str) -> None:
        self.circuit_breaker_transitions_total.labels(agent, from_state, to_state).inc()

    def record_ips_cache_hit(self, freshness: str, age_hours: float | None = None) -> None:
        self.ips_cache_hit_total.labels(freshness).inc()
        self._ips_hits += 1
        if age_hours is not None:
            safe_age = max(0.0, float(age_hours))
            self.ips_age_hours.observe(safe_age)
            self._ips_age_hours.append(safe_age)
            if len(self._ips_age_hours) > self._max_latency_window:
                self._ips_age_hours = self._ips_age_hours[-self._max_latency_window :]

    def record_ips_cache_miss(self, reason: str) -> None:
        self.ips_cache_miss_total.labels(reason).inc()
        self._ips_misses += 1

    def record_ips_load(self, duration_seconds: float) -> None:
        self.ips_load_duration_seconds.observe(max(0.0, float(duration_seconds)))

    def record_alert_received(self, source_agent: str, severity: str) -> None:
        self.alerts_received_total.labels(source_agent, severity).inc()

    def set_alerts_pending(self, severity: str, count: float) -> None:
        safe_count = max(0.0, float(count))
        self._alerts_pending_state[severity] = safe_count
        self.alerts_pending.labels(severity).set(safe_count)

    def record_alert_ack(self, severity: str, acknowledgment_seconds: float) -> None:
        ack = max(0.0, float(acknowledgment_seconds))
        self.alert_acknowledgment_seconds.labels(severity).observe(ack)
        bucket = self._alert_ack_seconds.setdefault(severity, [])
        bucket.append(ack)
        if len(bucket) > self._max_latency_window:
            self._alert_ack_seconds[severity] = bucket[-self._max_latency_window :]

    def record_alert_escalated(self, severity: str) -> None:
        self.alerts_escalated_total.labels(severity).inc()

    def record_workflow_execution(
        self,
        workflow_id: str,
        status: str,
        duration_seconds: float | None = None,
        iterations: int | None = None,
    ) -> None:
        self.workflow_executions_total.labels(workflow_id, status).inc()
        if duration_seconds is not None:
            self.workflow_duration_seconds.labels(workflow_id).observe(max(0.0, float(duration_seconds)))
        if iterations is not None:
            self.workflow_iterations.labels(workflow_id).observe(max(0, int(iterations)))

    def summary(self) -> dict[str, object]:
        agents_summary = {}
        for agent, stats in self._agent_stats.items():
            total = int(stats["total"])
            success = int(stats["success"])
            avg_latency = (stats["latency_sum"] / stats["latency_count"]) if stats["latency_count"] > 0 else None
            agents_summary[agent] = {
                "total_calls": total,
                "success_rate": (success / total) if total > 0 else None,
                "avg_latency_ms": round(avg_latency * 1000, 2) if avg_latency is not None else None,
            }

        return {
            "metrics_enabled": True,
            "tracked": [
                "wanda_orchestration_requests_total",
                "wanda_orchestration_duration_seconds",
                "wanda_orchestration_in_flight",
                "wanda_agent_calls_total",
                "wanda_circuit_breaker_state",
                "wanda_routing_decisions_total",
                "wanda_routing_llm_confidence",
                "wanda_routing_fallback_total",
                "wanda_ips_cache_hit_total",
                "wanda_ips_cache_miss_total",
                "wanda_alerts_received_total",
                "wanda_alerts_pending",
                "wanda_alert_acknowledgment_seconds",
                "wanda_alerts_escalated_total",
                "wanda_workflow_executions_total",
                "wanda_workflow_duration_seconds",
                "wanda_workflow_iterations",
            ],
            "slos": self.slos(),
            "agents": agents_summary,
            "ips_cache": self._ips_summary(),
            "routing": self._routing_summary(),
            "alerts": self._alerts_summary(),
        }

    def slos(self) -> dict[str, object]:
        p95_latency = self._percentile(self._latency_seconds, 0.95)
        availability = (self._orchestration_success / self._orchestration_total) if self._orchestration_total > 0 else None
        agent_availability = (self._agent_success / self._agent_total) if self._agent_total > 0 else None
        critical_ack_p95 = self._percentile(self._alert_ack_seconds.get("critical", []), 0.95)
        return {
            "p95_latency_seconds": {
                "value": p95_latency,
                "threshold": 5.0,
                "ok": (p95_latency is None) or (p95_latency <= 5.0),
            },
            "availability_ratio": {
                "value": availability,
                "threshold": 0.995,
                "ok": (availability is None) or (availability >= 0.995),
            },
            "agent_availability_ratio": {
                "value": agent_availability,
                "threshold": 0.98,
                "ok": (agent_availability is None) or (agent_availability >= 0.98),
            },
            "critical_alert_ack_seconds": {
                "value": critical_ack_p95,
                "threshold": 300.0,
                "ok": (critical_ack_p95 is None) or (critical_ack_p95 <= 300.0),
            },
        }

    def slos_snapshot(self) -> dict[str, object]:
        snapshot = {
            "timestamp": datetime.utcnow().isoformat(),
            "slos": self.slos(),
        }
        self._slo_history.append(snapshot)
        self._slo_history = self._slo_history[-self._history_limit :]
        self._history_store.append(snapshot)
        return snapshot

    def slos_history(self, limit: int = 50) -> list[dict[str, object]]:
        safe_limit = max(1, min(limit, self._history_limit))
        persisted = self._history_store.list(limit=safe_limit)
        if persisted:
            return persisted
        return self._slo_history[-safe_limit:]

    @staticmethod
    def _percentile(values: list[float], p: float) -> float | None:
        if not values:
            return None
        ordered = sorted(values)
        rank = max(1, ceil(p * len(ordered)))
        return float(ordered[rank - 1])

    def _ips_summary(self) -> dict[str, object]:
        total = self._ips_hits + self._ips_misses
        hit_rate = (self._ips_hits / total) if total > 0 else None
        avg_age = (sum(self._ips_age_hours) / len(self._ips_age_hours)) if self._ips_age_hours else None
        return {
            "hit_rate": hit_rate,
            "avg_age_hours": avg_age,
            "hits": self._ips_hits,
            "misses": self._ips_misses,
        }

    def _routing_summary(self) -> dict[str, object]:
        total = sum(self._routing_stats.values())
        llm = self._routing_stats.get("llm", 0)
        keyword = self._routing_stats.get("keyword", 0)
        return {
            "llm_rate": (llm / total) if total > 0 else None,
            "keyword_rate": (keyword / total) if total > 0 else None,
            "avg_confidence": (sum(self._routing_confidences) / len(self._routing_confidences))
            if self._routing_confidences
            else None,
        }

    def _alerts_summary(self) -> dict[str, object]:
        critical_pending = self._alerts_pending_state.get("critical", 0.0)
        high_pending = self._alerts_pending_state.get("high", 0.0)
        all_ack = [value for items in self._alert_ack_seconds.values() for value in items]
        avg_ack_minutes = (sum(all_ack) / len(all_ack) / 60.0) if all_ack else None
        return {
            "critical_pending": critical_pending,
            "high_pending": high_pending,
            "avg_ack_time_minutes": avg_ack_minutes,
        }
