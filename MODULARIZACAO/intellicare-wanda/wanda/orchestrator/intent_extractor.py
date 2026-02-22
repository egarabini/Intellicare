"""Intent extraction for query routing (EF-W003) — deterministic, no LLM required."""

import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class IntentResult:
    """Result of intent extraction from a query."""

    primary_intent: str                        # Main intent category
    secondary_intents: list[str] = field(default_factory=list)  # Additional intents
    urgency: str = "normal"                    # normal | high | emergency
    keywords_matched: list[str] = field(default_factory=list)
    is_multi_intent: bool = False

    @property
    def is_emergency(self) -> bool:
        return self.urgency == "emergency"

    @property
    def is_high_priority(self) -> bool:
        return self.urgency in ("high", "emergency")


# ── Intent Categories ──────────────────────────────────────────────────────

INTENT_KEYWORDS: dict[str, list[str]] = {
    "care_management": [
        "plano de cuidado", "plano cuidado", "lembrete", "tarefa", "adesao",
        "adesão", "horario", "horário", "agenda", "consulta agendada",
        "acompanhamento", "monitoramento", "jornada", "educacao", "orientacao",
        "educação", "orientação", "exercicio", "dieta", "o que devo fazer",
        "o que fazer", "como cuidar", "como tomar",
    ],
    "clinical_analysis": [
        "exame", "laboratorio", "laboratório", "resultado", "hemograma",
        "colesterol", "trigliceride", "triglicerídeo", "funcao renal",
        "função renal", "funcao hepatica", "função hepática", "analise clinica",
        "análise clínica", "tendencia", "correlacao", "correlação", "evolucao",
        "evolução", "painel", "labs", "interpretacao", "interpretação",
        "referencia", "referência", "urina", "sangue", "biopsia", "biópsia",
    ],
    "chronic_disease": [
        "drc", "ckd", "doenca renal", "doença renal", "diabetes", "dm2",
        "hipertensao", "hipertensão", "has", "pressao alta", "pressão alta",
        "creatinina", "tfg", "hemoglobina glicada", "hba1c", "glicose",
        "glicemia", "estagio", "estágio", "estadiamento", "nefro",
        "proteinuria", "proteinúria", "doenca cronica", "doença crônica",
    ],
    "territorial": [
        "cnes", "estabelecimento", "unidade de saude", "unidade de saúde",
        "ubs", "upa", "hospital", "regiao", "região", "territorial", "cidade",
        "municipio", "município", "datasus", "populacao", "população",
        "epidemiologia", "dados publicos", "dados públicos", "rede",
    ],
    "quality": [
        "qualidade", "indicador", "pilar", "donabedian", "estrutura",
        "processo", "resultado", "avaliacao", "avaliação", "pmaq",
        "iqasus", "meta", "desempenho", "eficiencia", "eficiência",
        "conformidade",
    ],
}

EMERGENCY_KEYWORDS: list[str] = [
    "emergencia", "emergência", "urgente", "urgencia", "urgência",
    "imediato", "agora", "dor forte", "dor intensa", "sem ar",
    "falta de ar", "desmaio", "desmaiei", "convulsao", "convulsão",
    "choque", "inconsciente", "nao respira", "não respira",
    "sangramento", "hemorragia",
]

HIGH_PRIORITY_KEYWORDS: list[str] = [
    "piora", "piorou", "deterioracao", "deterioração", "muito pior",
    "preocupado", "preocupante", "grave", "critico", "crítico",
    "internacao", "internação", "hospital",
]

# Default intent when nothing matches
DEFAULT_INTENT = "general"


class IntentExtractor:
    """Extracts intent from healthcare queries — deterministic, no LLM.

    Used to:
    1. Provide context to the LLM router (pre-filter)
    2. Classify urgency for safety escalation
    3. Serve as pure keyword fallback when LLM is unavailable

    All processing is synchronous and fast (< 1ms).
    """

    def extract_intent(self, query: str) -> IntentResult:
        """Extract primary and secondary intents from a query.

        Args:
            query: The user's query string (any language, but optimized for PT-BR).

        Returns:
            IntentResult with categorized intent and urgency.
        """
        query_lower = query.lower()

        # Check urgency first (most important)
        urgency = self._classify_urgency(query_lower)

        # Score each category
        scores: dict[str, int] = {}
        matched_keywords: list[str] = []

        for category, keywords in INTENT_KEYWORDS.items():
            hits = [kw for kw in keywords if kw in query_lower]
            if hits:
                scores[category] = len(hits)
                matched_keywords.extend(hits)

        if not scores:
            return IntentResult(
                primary_intent=DEFAULT_INTENT,
                urgency=urgency,
                keywords_matched=[],
            )

        # Sort by score
        sorted_intents = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        primary = sorted_intents[0][0]
        secondary = [cat for cat, _ in sorted_intents[1:]]

        return IntentResult(
            primary_intent=primary,
            secondary_intents=secondary,
            urgency=urgency,
            keywords_matched=list(set(matched_keywords))[:10],
            is_multi_intent=len(scores) > 1,
        )

    def classify_urgency(self, query: str) -> str:
        """Classify query urgency level.

        Returns:
            "emergency" | "high" | "normal"
        """
        return self._classify_urgency(query.lower())

    def _classify_urgency(self, query_lower: str) -> str:
        if any(kw in query_lower for kw in EMERGENCY_KEYWORDS):
            return "emergency"
        if any(kw in query_lower for kw in HIGH_PRIORITY_KEYWORDS):
            return "high"
        return "normal"

    def intent_to_modules(self, intent: IntentResult) -> list[str]:
        """Map intent categories to recommended module names.

        Used as fallback when LLM routing is unavailable.
        """
        INTENT_MODULE_MAP = {
            "care_management": "intellicare-geralda",
            "clinical_analysis": "intellicare-florence",
            "chronic_disease": "intellicare-oswaldo",
            "territorial": "intellicare-zilda",
            "quality": "intellicare-donabedian",
        }

        modules = []
        primary_module = INTENT_MODULE_MAP.get(intent.primary_intent)
        if primary_module:
            modules.append(primary_module)

        for secondary in intent.secondary_intents[:2]:  # Max 2 secondary
            mod = INTENT_MODULE_MAP.get(secondary)
            if mod and mod not in modules:
                modules.append(mod)

        return modules
