"""Florence IA — Sugestão SOAP (Hybrid: sugere, clínico decide salvar)."""
from __future__ import annotations

from intellicare_core.contracts.base import TenantContext
from modules.florence.contracts import SuggestRequest, SOAPSuggestion
from modules.shared.llm import call_llm

SOAP_PROMPT = """
Você é um assistente clínico. Com base nas informações abaixo, preencha os campos
SOAP de forma objetiva e concisa, em português, para uma nota clínica médica.

Motivo da consulta: {chief_complaint}
Motivo do agendamento: {appointment_reason}
Notas anteriores relevantes: {recent_notes}

Responda APENAS com um JSON no formato:
{{"S": "...", "O": "...", "A": "...", "P": "..."}}
"""


async def suggest_soap(ctx: TenantContext, req: SuggestRequest) -> SOAPSuggestion:
    prompt = SOAP_PROMPT.format(
        chief_complaint=req.chief_complaint,
        appointment_reason=req.appointment_reason or "não informado",
        recent_notes="\n".join(req.recent_notes or []) or "nenhuma",
    )

    try:
        result = await call_llm(prompt)
        confidence = "high"
    except Exception:
        result = _rule_based_suggestion(req)
        confidence = "low"

    return SOAPSuggestion(
        soap_s=result.get("S", ""),
        soap_o=result.get("O", ""),
        soap_a=result.get("A", ""),
        soap_p=result.get("P", ""),
        model=result.get("model", "rule-based"),
        confidence=confidence,
    )


def _rule_based_suggestion(req: SuggestRequest) -> dict:
    """Fallback determinístico quando LLM não está configurado."""
    return {
        "S": req.chief_complaint,
        "O": "Exame físico a ser preenchido pelo clínico.",
        "A": "Avaliação a ser preenchida pelo clínico.",
        "P": "Conduta a ser definida pelo clínico.",
        "model": "rule-based",
    }
