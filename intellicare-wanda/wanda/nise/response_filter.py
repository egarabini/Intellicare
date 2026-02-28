"""Response filter — detects dangerous patterns in FLOWISE responses (EF-W013)."""

from __future__ import annotations

import re

from wanda.nise.models import FilterResult

# Patterns that indicate medically dangerous advice — response must be blocked
_DANGER_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\b(pare|stop|discontinu)\b.{0,30}\b(medicament|remedio|insulina|insulin)\b", re.IGNORECASE),
    re.compile(r"\b(aument|reduz|doble|triple|duplic).{0,30}\b(dose|dosagem|comprimido)\b", re.IGNORECASE),
    re.compile(r"\b(nao\s+precisa|no\s+need).{0,30}(medico|doctor|hospital)\b", re.IGNORECASE),
    re.compile(r"\b(auto.?medic)\b", re.IGNORECASE),
    re.compile(r"\b(injet.{0,15}insulina\s+sem)\b", re.IGNORECASE),
    re.compile(r"\b(ignore|ignora)\b.{0,30}\b(prescrição|receita|bula)\b", re.IGNORECASE),
]

# Keywords that trigger escalation to AlertHub
_ESCALATION_KEYWORDS: list[re.Pattern[str]] = [
    re.compile(r"\b(emergência|emergencia|emergência)\b", re.IGNORECASE),
    re.compile(r"\b(dor\s+no\s+peito|chest\s+pain)\b", re.IGNORECASE),
    re.compile(r"\b(falta\s+de\s+ar|shortness\s+of\s+breath)\b", re.IGNORECASE),
    re.compile(r"\b(desmai|unconsci|inconscien)\b", re.IGNORECASE),
    re.compile(r"\b(suicid|me\s+matar|quero\s+morrer)\b", re.IGNORECASE),
    re.compile(r"\b(sangramento\s+intenso|bleeding\s+heavily)\b", re.IGNORECASE),
    re.compile(r"\b(convuls|seizure|ataque\s+epilét)\b", re.IGNORECASE),
]

_SAFE_FALLBACK = (
    "Entendo sua preocupação. Para orientações sobre medicamentos ou alterações no tratamento, "
    "por favor consulte seu médico ou enfermeiro. Posso ajudar com informações gerais sobre sua condição."
)


class NiseResponseFilter:
    """Filters FLOWISE responses for dangerous medical advice.

    - If DANGER_PATTERN matches → block response, return safe fallback
    - If ESCALATION_KEYWORD found → flag for escalation to AlertHub
    """

    def filter(self, response_text: str) -> FilterResult:
        flagged_patterns: list[str] = []
        requires_escalation = False

        # Check danger patterns
        for pattern in _DANGER_PATTERNS:
            m = pattern.search(response_text)
            if m:
                flagged_patterns.append(m.group(0)[:60])

        # Check escalation keywords
        for pattern in _ESCALATION_KEYWORDS:
            if pattern.search(response_text):
                requires_escalation = True
                break

        if flagged_patterns:
            return FilterResult(
                safe=False,
                filtered_text=_SAFE_FALLBACK,
                flagged_patterns=flagged_patterns,
                requires_escalation=requires_escalation,
            )

        return FilterResult(
            safe=True,
            filtered_text=response_text,
            flagged_patterns=[],
            requires_escalation=requires_escalation,
        )
