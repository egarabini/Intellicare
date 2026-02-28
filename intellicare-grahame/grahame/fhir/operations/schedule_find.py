"""Schedule/$find — busca slots disponíveis (W9-B)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from grahame.models.fhir_resource import FHIRResource


async def schedule_find(
    session: AsyncSession,
    actor_ref: str | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
    service_type: str | None = None,
    tenant_id: str | None = None,
) -> dict:
    """Implementa Schedule/$find — retorna Bundle com Slots disponíveis.

    Busca Schedules por actor (Practitioner ou HealthcareService),
    gera ou consulta Slots no período e filtra por status=free.
    """
    # 1. Buscar Schedules que referenciam o actor
    schedule_query = select(FHIRResource).where(
        FHIRResource.resource_type == "Schedule",
        FHIRResource.active == True,  # noqa: E712
    )
    if tenant_id:
        schedule_query = schedule_query.where(FHIRResource.tenant_id == tenant_id)

    result = await session.execute(schedule_query)
    schedules = list(result.scalars().all())

    if actor_ref:
        ref = actor_ref if "/" in actor_ref else f"Practitioner/{actor_ref}"
        schedules = [
            s
            for s in schedules
            if _schedule_references_actor(s.resource, ref)
        ]

    if not schedules:
        return _empty_bundle()

    # 2. Buscar Slots associados aos Schedules
    schedule_ids = [s.fhir_id for s in schedules]
    slot_query = select(FHIRResource).where(
        FHIRResource.resource_type == "Slot",
        FHIRResource.active == True,  # noqa: E712
    )
    if tenant_id:
        slot_query = slot_query.where(FHIRResource.tenant_id == tenant_id)

    slot_result = await session.execute(slot_query)
    all_slots = list(slot_result.scalars().all())

    # Filtrar slots por schedule e período
    slots = []
    for slot_row in all_slots:
        slot = slot_row.resource
        if slot.get("status") != "free":
            continue
        schedule_ref = slot.get("schedule", {}).get("reference", "")
        if not any(f"Schedule/{sid}" in schedule_ref for sid in schedule_ids):
            continue
        slot_start = slot.get("start")
        slot_end = slot.get("end")
        if start and slot_end:
            if _parse_dt(slot_end) <= start:
                continue
        if end and slot_start:
            if _parse_dt(slot_start) >= end:
                continue
        slots.append(slot)

    return _bundle_from_slots(slots)


def _schedule_references_actor(schedule: dict, actor_ref: str) -> bool:
    """Verifica se Schedule referencia o actor."""
    for actor in schedule.get("actor", []):
        ref = actor.get("reference", "") if isinstance(actor, dict) else ""
        if ref and actor_ref in ref:
            return True
    return False


def _parse_dt(s: str) -> datetime | None:
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


def _empty_bundle() -> dict:
    return {
        "resourceType": "Bundle",
        "type": "searchset",
        "total": 0,
        "entry": [],
    }


def _bundle_from_slots(slots: list[dict]) -> dict:
    entries = [
        {"fullUrl": f"Slot/{s.get('id', '')}", "resource": s}
        for s in slots
    ]
    return {
        "resourceType": "Bundle",
        "type": "searchset",
        "total": len(entries),
        "entry": entries,
    }
