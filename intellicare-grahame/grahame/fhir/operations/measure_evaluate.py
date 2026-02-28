"""$evaluate-measure — avalia uma Measure FHIR contra dados reais de pacientes."""

import uuid
from datetime import date, datetime, timezone
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from grahame.fhir.compartment import get_patient_ref, resource_belongs_to_patient
from grahame.models.fhir_resource import FHIRResource


async def evaluate_measure(
    measure_id: str,
    period_start: date,
    period_end: date,
    session: AsyncSession,
    tenant_id: str | None = None,
    subject: Optional[str] = None,
) -> dict:
    """Implementa Measure/$evaluate-measure — FHIR R4.

    Fluxo:
    1. Carregar Measure por id
    2. Determinar sujeitos (Patient ou Group)
    3. Para cada population group da Measure:
       a. Avaliar initial-population
       b. Avaliar denominator
       c. Avaliar numerator
       d. Calcular score = numerator / denominator
    4. Montar MeasureReport
    """
    # 1. Carregar Measure
    q = select(FHIRResource).where(
        FHIRResource.resource_type == "Measure",
        FHIRResource.fhir_id == measure_id,
        FHIRResource.active == True,  # noqa: E712
    )
    if tenant_id:
        q = q.where(FHIRResource.tenant_id == tenant_id)
    result = await session.execute(q)
    measure_row = result.scalar_one_or_none()

    if not measure_row:
        raise HTTPException(status_code=404, detail=f"Measure/{measure_id} not found")

    measure = measure_row.resource

    # 2. Determinar sujeitos
    patient_ids = await _resolve_subjects(session, tenant_id, subject)

    # 3. Avaliar grupos da Measure
    measure_groups = measure.get("group", [])
    report_groups = []

    for group in measure_groups:
        group_id = group.get("id", str(uuid.uuid4()))
        populations = group.get("population", [])
        pop_map = _index_populations(populations)

        # Avaliar cada população
        initial_pop_count = await _evaluate_population(
            pop_map.get("initial-population"),
            patient_ids,
            session,
            tenant_id,
            period_start,
            period_end,
        )
        denominator_count = await _evaluate_population(
            pop_map.get("denominator"),
            patient_ids,
            session,
            tenant_id,
            period_start,
            period_end,
        )
        numerator_count = await _evaluate_population(
            pop_map.get("numerator"),
            patient_ids,
            session,
            tenant_id,
            period_start,
            period_end,
        )

        # Calcular score
        score = None
        if denominator_count and denominator_count > 0 and numerator_count is not None:
            score = round(numerator_count / denominator_count, 4)

        report_group = {
            "id": group_id,
            "population": [],
        }

        if initial_pop_count is not None:
            report_group["population"].append(_pop_result("initial-population", initial_pop_count))
        if denominator_count is not None:
            report_group["population"].append(_pop_result("denominator", denominator_count))
        if numerator_count is not None:
            report_group["population"].append(_pop_result("numerator", numerator_count))

        if score is not None:
            report_group["measureScore"] = {"value": score, "unit": "1", "system": "http://unitsofmeasure.org", "code": "1"}

        report_groups.append(report_group)

    # 4. Montar MeasureReport
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    measure_report = {
        "resourceType": "MeasureReport",
        "id": str(uuid.uuid4()),
        "status": "complete",
        "type": "summary",
        "measure": f"Measure/{measure_id}",
        "date": now_iso,
        "period": {
            "start": period_start.isoformat(),
            "end": period_end.isoformat(),
        },
        "group": report_groups,
    }

    if subject:
        measure_report["subject"] = {"reference": subject}

    return measure_report


def _index_populations(populations: list) -> dict[str, dict]:
    """Indexa populações por code."""
    result = {}
    for pop in populations:
        for coding in pop.get("code", {}).get("coding", []):
            code = coding.get("code")
            if code:
                result[code] = pop
    return result


def _pop_result(code: str, count: int) -> dict:
    return {
        "code": {
            "coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/measure-population",
                "code": code,
            }]
        },
        "count": count,
    }


async def _resolve_subjects(
    session: AsyncSession,
    tenant_id: str | None,
    subject: Optional[str],
) -> list[str]:
    """Retorna lista de patient_ids a avaliar."""
    if subject:
        if subject.startswith("Patient/"):
            return [subject.split("/")[1]]
        if subject.startswith("Group/"):
            return await _expand_group(session, tenant_id, subject.split("/")[1])
        return [subject]

    # Sem subject → todos os pacientes do tenant
    q = select(FHIRResource).where(
        FHIRResource.resource_type == "Patient",
        FHIRResource.active == True,  # noqa: E712
    )
    if tenant_id:
        q = q.where(FHIRResource.tenant_id == tenant_id)
    result = await session.execute(q)
    return [row.fhir_id for row in result.scalars().all()]


async def _expand_group(
    session: AsyncSession,
    tenant_id: str | None,
    group_id: str,
) -> list[str]:
    """Expande um Group FHIR em lista de patient IDs."""
    q = select(FHIRResource).where(
        FHIRResource.resource_type == "Group",
        FHIRResource.fhir_id == group_id,
        FHIRResource.active == True,  # noqa: E712
    )
    if tenant_id:
        q = q.where(FHIRResource.tenant_id == tenant_id)
    result = await session.execute(q)
    row = result.scalar_one_or_none()
    if not row:
        return []

    patient_ids = []
    for member in row.resource.get("member", []):
        ref = member.get("entity", {}).get("reference", "")
        if ref.startswith("Patient/"):
            patient_ids.append(ref.split("/")[1])
    return patient_ids


async def _evaluate_population(
    population_def: Optional[dict],
    patient_ids: list[str],
    session: AsyncSession,
    tenant_id: str | None,
    period_start: date,
    period_end: date,
) -> Optional[int]:
    """Avalia critérios de uma população contra os sujeitos.

    Implementação simplificada: conta pacientes que possuem recursos no período.
    O Measure.group.population.criteria.expression seria avaliado aqui em uma
    implementação completa (FHIRPath / CQL). Aqui usamos lógica heurística.
    """
    if population_def is None:
        return None

    criteria = population_def.get("criteria", {})
    expression = criteria.get("expression", "")
    language = criteria.get("language", "")

    count = 0
    for patient_id in patient_ids:
        patient_ref = get_patient_ref(patient_id)
        if await _patient_meets_criteria(
            patient_id, patient_ref, expression, language,
            session, tenant_id, period_start, period_end
        ):
            count += 1

    return count


async def _patient_meets_criteria(
    patient_id: str,
    patient_ref: str,
    expression: str,
    language: str,
    session: AsyncSession,
    tenant_id: str | None,
    period_start: date,
    period_end: date,
) -> bool:
    """Verifica se um paciente atende os critérios.

    Heurística: qualquer paciente com pelo menos 1 recurso no período = incluso
    na initial-population. Denominador/numerador usariam CQL completo.
    """
    # Para initial-population: sempre inclui paciente que existe
    if not expression or expression.lower().strip() in ("true", "1"):
        return True

    # Estratégia básica: busca recursos associados ao paciente no período
    q = select(FHIRResource).where(
        FHIRResource.active == True,  # noqa: E712
    )
    if tenant_id:
        q = q.where(FHIRResource.tenant_id == tenant_id)
    result = await session.execute(q)

    for row in result.scalars().all():
        if not resource_belongs_to_patient(row.resource, patient_ref):
            continue
        # Verificar se está no período
        updated = row.updated_at
        if isinstance(updated, datetime):
            rec_date = updated.date()
            if period_start <= rec_date <= period_end:
                return True

    return False
