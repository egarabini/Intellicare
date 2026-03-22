"""Oswaldo IA — Sugestão de CID-10 e Prescrição (Hybrid)."""
from __future__ import annotations

import json
import logging
from uuid import UUID

from intellicare_core.contracts.base import TenantContext
from modules.cuidado.service import CuidadoService
from modules.marie.client import call_marie, is_marie_enabled
from modules.oswaldo.contracts import (
    OswaldoSuggestRequest, OswaldoSuggestion, PrescriptionItem,
)
from modules.shared.llm import call_llm, get_prompt_template

logger = logging.getLogger("intellicare.oswaldo.services")
_CUIDADO_SERVICE = CuidadoService()

OSWALDO_CID10_PROMPT_FALLBACK = """
Você é um assistente clínico. Com base nas informações abaixo, sugira:
1. O CID-10 mais provável (código e descrição curta)
"""

OSWALDO_PRESCRIPTION_PROMPT_FALLBACK = """
2. Uma prescrição inicial com até 3 itens (medicamento, posologia, duração)

Queixa principal: {chief_complaint}
Diagnósticos anteriores: {recent_diagnoses}
Medicamentos em uso: {current_medications}

Responda APENAS com JSON no formato:
{{
  "cid10_code": "X00",
  "cid10_desc": "Descrição curta",
  "items": [
    {{"drug": "Nome 500mg", "posology": "1 comp 8/8h", "duration": "5 dias"}}
  ]
}}
"""


async def suggest(ctx: TenantContext, req: OswaldoSuggestRequest) -> OswaldoSuggestion:
    marie_result: dict | None = None
    patient_uuid = _coerce_patient_uuid(req.patient_id)

    if is_marie_enabled() and patient_uuid is not None:
        marie_response = await call_marie(
            workflow_slug="cid10_rag",
            inputs={
                "query": req.chief_complaint,
                "patient_history": await _get_patient_timeline_summary(ctx, patient_uuid),
            },
        )
        marie_result = _parse_marie_cid10_response(marie_response)

    result, confidence = await _local_suggestion(req)
    if marie_result:
        result["cid10_code"] = marie_result["cid10_code"]
        result["cid10_desc"] = marie_result["cid10_desc"]
        result["model"] = marie_result.get("model", "marie")
        confidence = "high"

    return OswaldoSuggestion(
        cid10_code=result.get("cid10_code", "Z00"),
        cid10_desc=result.get("cid10_desc", "Consulta de rotina"),
        prescription_items=[PrescriptionItem(**i) for i in result.get("items", [])],
        model=result.get("model", "rule-based"),
        confidence=confidence,
    )


async def _local_suggestion(req: OswaldoSuggestRequest) -> tuple[dict, str]:
    cid10_prompt = await get_prompt_template("oswaldo_cid10", OSWALDO_CID10_PROMPT_FALLBACK)
    prescription_prompt = await get_prompt_template("oswaldo_prescription", OSWALDO_PRESCRIPTION_PROMPT_FALLBACK)
    prompt = f"{cid10_prompt.strip()}\n{prescription_prompt.strip()}".format(
        chief_complaint=req.chief_complaint,
        recent_diagnoses=", ".join(req.recent_diagnoses or []) or "nenhum",
        current_medications=", ".join(req.current_medications or []) or "nenhum",
    )
    try:
        return await call_llm(prompt), "high"
    except Exception:
        return _rule_based_suggestion(req), "low"


def _coerce_patient_uuid(patient_id: str | int) -> UUID | None:
    try:
        return UUID(str(patient_id))
    except (TypeError, ValueError):
        return None


async def _get_patient_timeline_summary(ctx: TenantContext, patient_id: UUID) -> str:
    try:
        timeline = await _CUIDADO_SERVICE.clinical_timeline(ctx, patient_id, limit=8, offset=0)
    except Exception:
        logger.debug("Falha ao buscar timeline para Marie", exc_info=True)
        return ""

    lines: list[str] = []
    for item in timeline.get("items", []):
        title = item.get("title") or item.get("event_type") or "evento"
        subtitle = item.get("subtitle") or ""
        status = item.get("status") or ""
        line = f"- {title}"
        if subtitle:
            line += f": {subtitle}"
        if status:
            line += f" [{status}]"
        lines.append(line)

    summary = "\n".join(lines)
    return summary[:2000]


def _parse_marie_cid10_response(response: dict | None) -> dict | None:
    if not response:
        return None

    if isinstance(response.get("answer"), str):
        answer = response["answer"].strip()
        try:
            data = json.loads(answer)
            if data.get("cid10_code"):
                data["model"] = "marie"
                return data
        except json.JSONDecodeError:
            pass

    if response.get("cid10_code"):
        data = dict(response)
        data["model"] = "marie"
        return data

    outputs = response.get("outputs")
    if isinstance(outputs, dict) and outputs.get("cid10_code"):
        data = dict(outputs)
        data["model"] = "marie"
        return data

    return None


def _rule_based_suggestion(req: OswaldoSuggestRequest) -> dict:
    """Fallback determinístico quando LLM não está configurado."""
    return {
        "cid10_code": "Z00",
        "cid10_desc": "Consulta de rotina (preencher manualmente)",
        "items": [],
        "model": "rule-based",
    }
