"""Florence IA — Sugestão SOAP (Hybrid: sugere, clínico decide salvar)."""
from __future__ import annotations

import json
import logging
import re
from uuid import UUID

from intellicare_core.contracts.base import TenantContext
from modules.cuidado.service import CuidadoService
from modules.florence.contracts import SuggestRequest, SOAPSuggestion
from modules.marie.client import call_marie, is_marie_enabled
from modules.shared.llm import call_llm, get_prompt_template

logger = logging.getLogger("intellicare.florence.services")
_CUIDADO_SERVICE = CuidadoService()

SOAP_PROMPT_FALLBACK = """
Você é um assistente clínico. Com base nas informações abaixo, preencha os campos
SOAP de forma objetiva e concisa, em português, para uma nota clínica médica.
"""

FREE_TEXT_PROMPT_FALLBACK = """

Motivo da consulta: {chief_complaint}
Motivo do agendamento: {appointment_reason}
Notas anteriores relevantes: {recent_notes}

Responda APENAS com um JSON no formato:
{{"S": "...", "O": "...", "A": "...", "P": "..."}}
"""


async def suggest_soap(ctx: TenantContext, req: SuggestRequest) -> SOAPSuggestion:
    result: dict
    confidence: str

    if is_marie_enabled():
        marie_response = await call_marie(
            workflow_slug="florence_soap_rag",
            inputs={
                "chief_complaint": req.chief_complaint,
                "patient_history": await _get_florence_timeline_context(ctx, req.patient_id),
                "encounter_date": str(req.encounter_id),
            },
        )
        parsed = _parse_marie_soap_response(marie_response)
        if parsed:
            result = parsed
            confidence = "high"
        else:
            result, confidence = await _local_suggestion(req)
    else:
        result, confidence = await _local_suggestion(req)

    return SOAPSuggestion(
        soap_s=result.get("soap_s") or result.get("S", ""),
        soap_o=result.get("soap_o") or result.get("O", ""),
        soap_a=result.get("soap_a") or result.get("A", ""),
        soap_p=result.get("soap_p") or result.get("P", ""),
        model=result.get("model", "rule-based"),
        confidence=confidence,
    )


async def _local_suggestion(req: SuggestRequest) -> tuple[dict, str]:
    soap_prompt = await get_prompt_template("florence_soap", SOAP_PROMPT_FALLBACK)
    free_text_prompt = await get_prompt_template("florence_free_text", FREE_TEXT_PROMPT_FALLBACK)
    prompt = f"{soap_prompt.strip()}\n\n{free_text_prompt.strip()}".format(
        chief_complaint=req.chief_complaint,
        appointment_reason=req.appointment_reason or "não informado",
        recent_notes="\n".join(req.recent_notes or []) or "nenhuma",
    )
    try:
        return await call_llm(prompt), "high"
    except Exception:
        return _rule_based_suggestion(req), "low"


async def _get_florence_timeline_context(ctx: TenantContext, patient_id: str | int, days: int = 180) -> str:
    del days
    try:
        patient_uuid = UUID(str(patient_id))
    except (TypeError, ValueError):
        return ""

    try:
        timeline = await _CUIDADO_SERVICE.clinical_timeline(ctx, patient_uuid, limit=20, offset=0)
    except Exception:
        logger.debug("Falha ao buscar timeline para Florence/Marie", exc_info=True)
        return ""

    lines: list[str] = []
    for event in timeline.get("items", []):
        title = event.get("title") or event.get("event_type") or "evento"
        subtitle = event.get("subtitle") or ""
        metadata = event.get("metadata") or {}
        occurred_at = str(event.get("occurred_at") or "")[:10]

        if event.get("event_type") == "encounter":
            lines.append(f"[{occurred_at}] Consulta: {title} | CID: {metadata.get('cid10_code') or '-'}")
        elif event.get("event_type") == "prescription":
            lines.append(f"[{occurred_at}] Prescrição: {subtitle or metadata.get('cid10_code') or '-'}")
        elif event.get("event_type") == "clinical_note":
            lines.append(f"[{occurred_at}] Nota: {subtitle[:120]}")

    return "\n".join(lines)[:3000]


def _parse_marie_soap_response(response: dict | None) -> dict | None:
    if not response:
        return None

    if all(key in response for key in ("soap_s", "soap_o", "soap_a", "soap_p")):
        data = dict(response)
        data["model"] = "marie"
        return data

    answer = response.get("answer")
    if isinstance(answer, str):
        match = re.search(r"\{.*\}", answer, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(0))
                if all(key in data for key in ("soap_s", "soap_o", "soap_a", "soap_p")):
                    data["model"] = "marie"
                    return data
            except json.JSONDecodeError:
                return None

    return None


def _rule_based_suggestion(req: SuggestRequest) -> dict:
    """Fallback determinístico quando LLM não está configurado."""
    return {
        "S": req.chief_complaint,
        "O": "Exame físico a ser preenchido pelo clínico.",
        "A": "Avaliação a ser preenchida pelo clínico.",
        "P": "Conduta a ser definida pelo clínico.",
        "model": "rule-based",
    }


def generate_clinical_report(data: dict) -> bytes:
    """Gera PDF do encontro clínico. Retorna bytes."""
    from weasyprint import HTML
    from jinja2 import Environment, FileSystemLoader
    from datetime import datetime
    import os

    template_dir = os.path.join(os.path.dirname(__file__), "templates")
    env = Environment(loader=FileSystemLoader(template_dir))

    def strftime(value, fmt):
        if value is None:
            return ""
        if isinstance(value, str):
            value = datetime.fromisoformat(value.replace('Z', '+00:00'))
        return value.strftime(fmt)

    env.filters["strftime"] = strftime

    template = env.get_template("clinical_report.html")
    html_str = template.render(**data, generated_at=datetime.now())
    return HTML(string=html_str).write_pdf()
