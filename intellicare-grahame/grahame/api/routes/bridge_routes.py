"""Rotas de integração com adaptadores HIS (intellicare-bridge).

Endpoint principal: POST /fhir/$process-message
Aceita FHIR Bundle transaction/batch de adaptadores autenticados com role HIS_ADAPTER.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from grahame.api.deps import get_db, require_his_adapter
from grahame.services.fhir_service import FHIRService
from intellicare_core.bridge.context import HISContext

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/fhir", tags=["Bridge"])

STREAM_HIS_INGESTION = "intellicare:events:his_ingestion"


async def _publish_his_ingestion_event(
    request: Request,
    context: HISContext,
    entry_count: int,
) -> None:
    """Publica evento no Redis Stream para o WANDA processar."""
    rate_limiter = getattr(request.app.state, "rate_limiter", None)
    if not rate_limiter or not getattr(rate_limiter, "redis", None):
        logger.warning("Redis not available, skipping his_bundle_ingested event")
        return

    redis = rate_limiter.redis
    event = {
        "event_type": "his_bundle_ingested",
        "his_system": context.his_system.value if hasattr(context.his_system, "value") else str(context.his_system),
        "tenant_id": context.tenant_id,
        "fhir_patient_id": context.fhir_patient_id,
        "encounter_id": context.encounter_id,
        "bundle_entry_count": str(entry_count),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    try:
        await redis.xadd(STREAM_HIS_INGESTION, event, maxlen=10000)
        logger.info("Published his_bundle_ingested event", extra=event)
    except Exception as e:
        logger.warning("Failed to publish his_bundle_ingested: %s", e)


@router.post(
    "/$process-message",
    summary="Ingestão de FHIR Bundle (adaptadores HIS)",
    status_code=202,
)
async def process_message_bundle(
    bundle: dict[str, Any],
    request: Request,
    session: AsyncSession = Depends(get_db),
    _: dict = Depends(require_his_adapter),
) -> dict[str, Any]:
    """Recebe FHIR Bundle transaction/batch de um adaptador HIS.

    Para cada entry do bundle:
    - Patient, Observation, Condition, MedicationRequest → upsert via FHIRService
    - Outros tipos → aceitos mas sem processamento especial (log + store)

    Publica evento 'his_bundle_ingested' no Redis Stream para WANDA.
    Retorna Bundle de respostas com OperationOutcome por entry.
    """
    his_context_header = request.headers.get("X-HIS-Context")
    his_context: HISContext | None = None
    if his_context_header:
        try:
            his_context = HISContext.from_header(his_context_header)
        except Exception:
            pass

    results = []
    tenant_id = his_context.tenant_id if his_context else None
    svc = FHIRService(session, tenant_id=tenant_id)

    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})
        resource_type = resource.get("resourceType", "Unknown")
        rid = resource.get("id", "unknown")

        try:
            if resource_type != "Unknown":
                await svc.upsert(resource)
        except Exception as e:
            logger.warning("Upsert failed for %s/%s: %s", resource_type, rid, e)
            results.append({
                "resourceType": "OperationOutcome",
                "issue": [{
                    "severity": "warning",
                    "code": "exception",
                    "diagnostics": str(e),
                }],
            })
            continue

        results.append({
            "resourceType": "OperationOutcome",
            "issue": [{
                "severity": "information",
                "code": "informational",
                "diagnostics": f"{resource_type} processado",
            }],
        })

    if his_context:
        await _publish_his_ingestion_event(request, his_context, len(results))

    return {
        "resourceType": "Bundle",
        "type": "transaction-response",
        "entry": [{"resource": r} for r in results],
    }
