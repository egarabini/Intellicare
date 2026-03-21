"""Metricas Prometheus do modulo CarePlanner."""
from __future__ import annotations

from prometheus_client import Counter, Histogram

careplanner_dispatch_total = Counter(
    "careplanner_dispatch_total",
    "Disparos de mensagem por tenant e status final",
    ["tenant_slug", "status", "channel"],
)

careplanner_event_total = Counter(
    "careplanner_event_total",
    "Eventos CarePlanner por tenant e tipo",
    ["tenant_slug", "event_type"],
)

careplanner_orphan_inbound_total = Counter(
    "careplanner_orphan_inbound_total",
    "Inbounds sem correlacao por tenant",
    ["tenant_slug"],
)

careplanner_video_session_total = Counter(
    "careplanner_video_session_total",
    "Videoconsultas abertas por tenant",
    ["tenant_slug"],
)

careplanner_dispatch_to_sent_seconds = Histogram(
    "careplanner_dispatch_to_sent_seconds",
    "Tempo entre DISPATCHED e SENT (confirmacao de entrega)",
    ["tenant_slug", "channel"],
    buckets=[1, 5, 10, 30, 60, 120, 300],
)

careplanner_inbound_to_close_seconds = Histogram(
    "careplanner_inbound_to_close_seconds",
    "Tempo entre REPLIED e CLOSED (resolucao da jornada)",
    ["tenant_slug"],
    buckets=[60, 300, 900, 1800, 3600, 7200, 86400],
)
