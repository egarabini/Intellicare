"""FastAPI router para CDS Hooks 2.0.

Endpoints:
    GET  /cds-services                        → Discovery (lista de serviços)
    POST /cds-services/{service_id}           → Invocar hook → Cards
    POST /cds-services/{service_id}/feedback  → Registrar feedback (real)
    GET  /cds-services/{service_id}/feedback-stats  → Estatísticas de feedback

Métricas Prometheus (opcionais — silenciosamente ignoradas se prometheus_client não instalado):
    cds_cards_generated_total   (labels: service_id, indicator)
    cds_feedback_received_total (labels: service_id, outcome)
"""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel

from intellicare_core.cds_hooks import CDSRequest, CDSResponse, CDSServiceRegistry
from grahame.cds_services.patient_view import PatientViewAlertsService
from grahame.cds_services.order_sign import OrderSignCheckerService

logger = logging.getLogger(__name__)

cds_router = APIRouter(prefix="/cds-services", tags=["CDS Hooks"])

# ── Registry singleton ─────────────────────────────────────────────────────────

_registry = CDSServiceRegistry()
_registry.register(PatientViewAlertsService())
_registry.register(OrderSignCheckerService())

# ── Prometheus metrics (opcional) ──────────────────────────────────────────────

try:
    from prometheus_client import Counter

    _cards_counter = Counter(
        "cds_cards_generated_total",
        "Total de cards CDS gerados",
        ["service_id", "indicator"],
    )
    _feedback_counter = Counter(
        "cds_feedback_received_total",
        "Total de feedbacks CDS recebidos",
        ["service_id", "outcome"],
    )
    _PROMETHEUS_AVAILABLE = True
except ImportError:
    _PROMETHEUS_AVAILABLE = False
    logger.debug("prometheus_client não instalado — métricas CDS desabilitadas")

# ── Feedback store in-memory ───────────────────────────────────────────────────
# {service_id: {outcome: count}}
_feedback_store: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

_VALID_OUTCOMES = {"accepted", "overridden", "no-action"}

# ── Discovery ──────────────────────────────────────────────────────────────────


class DiscoveryResponse(BaseModel):
    services: list[dict[str, Any]]


@cds_router.get(
    "",
    summary="CDS Hooks — Discovery",
    description=(
        "Retorna a lista de serviços CDS disponíveis conforme CDS Hooks 2.0. "
        "Utilizado pelo EHR para descobrir quais hooks o servidor suporta."
    ),
)
async def discovery() -> DiscoveryResponse:
    return DiscoveryResponse(
        services=[svc.model_dump(exclude_none=True) for svc in _registry.list_services()]
    )


# ── Hook invocation ────────────────────────────────────────────────────────────


@cds_router.post(
    "/{service_id}",
    response_model=CDSResponse,
    summary="CDS Hooks — Invocar serviço",
    description=(
        "Recebe uma chamada de hook do EHR e retorna cards de suporte à decisão. "
        "O body deve seguir o formato CDS Hooks 2.0 CDSRequest."
    ),
)
async def invoke_hook(service_id: str, body: CDSRequest) -> CDSResponse:
    response = _registry.call(service_id, body)
    if response is None:
        raise HTTPException(
            status_code=404,
            detail=f"CDS service '{service_id}' not found",
        )

    # Incrementar métricas por indicador
    if _PROMETHEUS_AVAILABLE:
        for card in response.cards:
            _cards_counter.labels(
                service_id=service_id, indicator=card.indicator
            ).inc()

    return response


# ── Feedback ───────────────────────────────────────────────────────────────────


class FeedbackEntry(BaseModel):
    card: str
    """UUID do card."""

    outcome: str
    """'accepted' | 'overridden' | 'no-action'"""

    acceptedSuggestions: list[dict[str, Any]] = []
    outcomeTimestamp: str = ""


class FeedbackBody(BaseModel):
    feedback: list[FeedbackEntry]


@cds_router.post(
    "/{service_id}/feedback",
    status_code=204,
    response_model=None,
    response_class=Response,
    summary="CDS Hooks — Feedback",
    description=(
        "Registra feedback do EHR sobre cards aceitos/ignorados/substituídos. "
        "Contabilizado em memória + Prometheus. "
        "Outcomes válidos: 'accepted', 'overridden', 'no-action'."
    ),
)
async def hook_feedback(service_id: str, body: FeedbackBody) -> Response:
    if service_id not in _registry:
        raise HTTPException(
            status_code=404, detail=f"CDS service '{service_id}' not found"
        )

    for entry in body.feedback:
        outcome = entry.outcome if entry.outcome in _VALID_OUTCOMES else "unknown"
        _feedback_store[service_id][outcome] += 1
        if _PROMETHEUS_AVAILABLE:
            _feedback_counter.labels(service_id=service_id, outcome=outcome).inc()

    logger.info(
        "cds.feedback service=%s entries=%d",
        service_id,
        len(body.feedback),
    )
    return Response(status_code=204)


# ── Feedback stats ─────────────────────────────────────────────────────────────


@cds_router.get(
    "/{service_id}/feedback-stats",
    summary="CDS Hooks — Estatísticas de Feedback",
    description="Retorna contagem acumulada de feedbacks por outcome para um serviço.",
)
async def feedback_stats(service_id: str) -> dict[str, Any]:
    if service_id not in _registry:
        raise HTTPException(
            status_code=404, detail=f"CDS service '{service_id}' not found"
        )
    counts = dict(_feedback_store.get(service_id, {}))
    total = sum(counts.values())
    return {
        "service_id": service_id,
        "total_feedback": total,
        "outcomes": counts,
    }
