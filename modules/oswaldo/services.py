"""Oswaldo IA — Sugestão de CID-10 e Prescrição (Hybrid)."""
from __future__ import annotations

from intellicare_core.contracts.base import TenantContext
from modules.oswaldo.contracts import (
    OswaldoSuggestRequest, OswaldoSuggestion, PrescriptionItem,
)
from modules.shared.llm import call_llm, get_prompt_template

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
    del ctx
    cid10_prompt = await get_prompt_template("oswaldo_cid10", OSWALDO_CID10_PROMPT_FALLBACK)
    prescription_prompt = await get_prompt_template("oswaldo_prescription", OSWALDO_PRESCRIPTION_PROMPT_FALLBACK)
    prompt = f"{cid10_prompt.strip()}\n{prescription_prompt.strip()}".format(
        chief_complaint=req.chief_complaint,
        recent_diagnoses=", ".join(req.recent_diagnoses or []) or "nenhum",
        current_medications=", ".join(req.current_medications or []) or "nenhum",
    )

    try:
        result = await call_llm(prompt)
        confidence = "high"
    except Exception:
        result = _rule_based_suggestion(req)
        confidence = "low"

    return OswaldoSuggestion(
        cid10_code=result.get("cid10_code", "Z00"),
        cid10_desc=result.get("cid10_desc", "Consulta de rotina"),
        prescription_items=[PrescriptionItem(**i) for i in result.get("items", [])],
        model=result.get("model", "rule-based"),
        confidence=confidence,
    )


def _rule_based_suggestion(req: OswaldoSuggestRequest) -> dict:
    """Fallback determinístico quando LLM não está configurado."""
    return {
        "cid10_code": "Z00",
        "cid10_desc": "Consulta de rotina (preencher manualmente)",
        "items": [],
        "model": "rule-based",
    }
