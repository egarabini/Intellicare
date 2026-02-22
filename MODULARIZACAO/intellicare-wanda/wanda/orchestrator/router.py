"""Query router — analisa a mensagem e decide quais modulos chamar."""

import re
from typing import Optional

from wanda.discovery.models import ModuleInfo, RoutingDecision

# Keyword mappings per module
ROUTING_KEYWORDS: dict[str, list[str]] = {
    "intellicare-oswaldo": [
        "doenca cronica", "diabetes", "pressao", "hipertensao",
        "renal", "rim", "rins", "creatinina", "drc", "ckd",
        "glicose", "hba1c", "hemoglobina glicada", "estadiamento",
        "alerta", "cronico", "has", "dm2", "nefro",
    ],
    "intellicare-florence": [
        "exame", "laboratorio", "resultado", "hemograma", "colesterol",
        "trigliceride", "funcao renal", "funcao hepatica", "analise clinica",
        "tendencia", "correlacao", "evolucao", "painel", "labs",
        "interpretacao", "referencia", "urina", "sangue",
    ],
    "intellicare-zilda": [
        "cnes", "estabelecimento", "unidade de saude", "ubs", "upa",
        "hospital", "regiao", "territorial", "cidade", "municipio",
        "datasus", "populacao", "epidemiologia", "dados publicos",
    ],
    "intellicare-geralda": [
        "plano de cuidado", "lembrete", "tarefa", "adesao",
        "medicamento", "horario", "educacao", "orientacao",
        "acompanhamento", "agenda", "consulta", "exercicio",
        "dieta", "monitoramento",
    ],
    "intellicare-donabedian": [
        "qualidade", "indicador", "pilar", "donabedian",
        "estrutura", "processo", "resultado", "avaliacao",
        "pmaq", "iqasus",
    ],
}

# Capability-based fallback
CAPABILITY_MAPPING: dict[str, str] = {
    "chronic-disease-monitoring": "intellicare-oswaldo",
    "chronic-disease": "intellicare-oswaldo",
    "clinical-analysis": "intellicare-florence",
    "lab-interpretation": "intellicare-florence",
    "labs": "intellicare-florence",
    "cnes-data": "intellicare-zilda",
    "territorial-analysis": "intellicare-zilda",
    "care-plans": "intellicare-geralda",
    "reminders": "intellicare-geralda",
    "education": "intellicare-geralda",
    "adherence-tracking": "intellicare-geralda",
    "quality-assessment": "intellicare-donabedian",
}


class QueryRouter:
    """Routes queries to appropriate modules using keyword analysis."""

    def __init__(self, max_modules: int = 3):
        self.max_modules = max_modules

    def route(
        self,
        query: str,
        available_modules: list[ModuleInfo],
        patient_id: Optional[str] = None,
    ) -> RoutingDecision:
        """Analyze a query and decide which modules to call."""
        query_lower = query.lower()
        available_names = {m.name for m in available_modules}

        # Score each module by keyword matches
        scores: dict[str, int] = {}
        for module_name, keywords in ROUTING_KEYWORDS.items():
            if module_name not in available_names:
                continue
            score = sum(1 for kw in keywords if kw in query_lower)
            if score > 0:
                scores[module_name] = score

        # If keyword match found, route to top scoring modules
        if scores:
            sorted_modules = sorted(scores.items(), key=lambda x: x[1], reverse=True)
            targets = [name for name, _ in sorted_modules[: self.max_modules]]
            top_score = sorted_modules[0][1]
            confidence = min(1.0, top_score / 3)
            return RoutingDecision(
                target_modules=targets,
                reason=f"Keyword match: {top_score} hit(s) para {targets[0]}",
                confidence=confidence,
            )

        # Fallback: capability-based routing
        capability_targets = set()
        for module in available_modules:
            for cap in module.capabilities:
                mapped = CAPABILITY_MAPPING.get(cap)
                if mapped and mapped in available_names:
                    capability_targets.add(mapped)

        if capability_targets:
            targets = list(capability_targets)[: self.max_modules]
            return RoutingDecision(
                target_modules=targets,
                reason="Fallback por capability — sem match de keyword",
                confidence=0.3,
            )

        # Last resort: if only one module, send to it
        if len(available_modules) == 1:
            return RoutingDecision(
                target_modules=[available_modules[0].name],
                reason="Unico modulo disponivel",
                confidence=0.5,
            )

        return RoutingDecision(
            target_modules=[],
            reason="Nenhum modulo adequado encontrado para a consulta",
            confidence=0.0,
        )

    def detect_clinical_intent(self, query: str) -> bool:
        """Detect if a query has clinical intent (needs IPS first)."""
        clinical_patterns = [
            r"paciente",
            r"exame",
            r"laboratorio",
            r"medicamento",
            r"diagnostico",
            r"sintoma",
            r"tratamento",
            r"doenca",
            r"analise clinica",
            r"como esta",
            r"evolucao",
        ]
        query_lower = query.lower()
        return any(re.search(p, query_lower) for p in clinical_patterns)
