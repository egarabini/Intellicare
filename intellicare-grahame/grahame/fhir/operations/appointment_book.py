"""Appointment/$book — reserva slot e cria Appointment (W9-B)."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from grahame.models.fhir_resource import FHIRResource
from grahame.services.fhir_service import FHIRService


async def appointment_book(
    session: AsyncSession,
    slot_ref: str,
    patient_ref: str,
    practitioner_ref: str | None = None,
    comment: str | None = None,
    tenant_id: str | None = None,
) -> dict:
    """Implementa Appointment/$book — reserva slot e cria Appointment.

    Valida que Slot existe e está free, cria Appointment, atualiza Slot para busy.
    Transação deve ser atômica (chamador deve usar commit/rollback).
    """
    slot_id = _extract_id(slot_ref, "Slot")
    patient_id = _extract_id(patient_ref, "Patient")

    svc = FHIRService(session, tenant_id=tenant_id)

    # 1. Buscar Slot
    try:
        slot_row = await svc.get("Slot", slot_id)
    except HTTPException as e:
        if e.status_code == 404:
            raise HTTPException(status_code=404, detail="Slot não encontrado")
        raise

    slot = slot_row.resource
    if slot.get("status") != "free":
        raise HTTPException(status_code=409, detail="Slot já está ocupado ou indisponível")

    # 2. Criar Appointment
    appointment_id = str(uuid.uuid4())[:8]
    appointment = {
        "resourceType": "Appointment",
        "id": appointment_id,
        "status": "booked",
        "slot": [{"reference": f"Slot/{slot_id}"}],
        "participant": [
            {"actor": {"reference": f"Patient/{patient_id}"}, "required": "required", "status": "accepted"},
        ],
    }
    if practitioner_ref:
        pract_id = _extract_id(practitioner_ref, "Practitioner")
        appointment["participant"].append(
            {"actor": {"reference": f"Practitioner/{pract_id}"}, "required": "optional", "status": "accepted"}
        )
    if comment:
        appointment["comment"] = comment

    await svc.upsert(appointment)

    # 3. Atualizar Slot para busy
    slot["status"] = "busy"
    slot["comment"] = f"Reservado para Appointment/{appointment_id}"
    await svc.upsert(slot)

    return appointment


def _extract_id(ref: str, resource_type: str) -> str:
    if "/" in ref:
        return ref.split("/")[-1]
    return ref


