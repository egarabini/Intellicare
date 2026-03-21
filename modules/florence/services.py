"""Florence IA — Sugestão SOAP (Hybrid: sugere, clínico decide salvar)."""
from __future__ import annotations

import json
import os

import httpx

from intellicare_core.contracts.base import TenantContext
from modules.florence.contracts import SuggestRequest, SOAPSuggestion

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
        result = await _call_llm(prompt)
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


async def _call_llm(prompt: str) -> dict:
    """Chama LLM OpenAI-compatible (Ollama, OpenAI, Groq, etc)."""
    url = os.getenv("FLORENCE_LLM_URL", "")
    api_key = os.getenv("FLORENCE_LLM_API_KEY", "")
    model = os.getenv("FLORENCE_LLM_MODEL", "gpt-4o-mini")

    if not url:
        raise RuntimeError("FLORENCE_LLM_URL not configured")

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            url,
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "response_format": {"type": "json_object"},
                "temperature": 0.3,
            },
        )
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]
        data = json.loads(content)
        data["model"] = model
        return data


def _rule_based_suggestion(req: SuggestRequest) -> dict:
    """Fallback determinístico quando LLM não está configurado."""
    return {
        "S": req.chief_complaint,
        "O": "Exame físico a ser preenchido pelo clínico.",
        "A": "Avaliação a ser preenchida pelo clínico.",
        "P": "Conduta a ser definida pelo clínico.",
        "model": "rule-based",
    }
