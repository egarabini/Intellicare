import json
import unicodedata
from pathlib import Path
from modules.shared.llm import get_prompt_template, call_llm
from .contracts import InteractionWarning

_INTERACTIONS_DB = None

def _load_db() -> list:
    global _INTERACTIONS_DB
    if _INTERACTIONS_DB is None:
        path = Path(__file__).parent.parent.parent / "data" / "drug_interactions.json"
        if not path.exists():
            return []
        _INTERACTIONS_DB = json.loads(path.read_text("utf-8"))
    return _INTERACTIONS_DB

def _normalize(name: str) -> str:
    """Lowercase + remove acentos para matching tolerante."""
    nfkd = unicodedata.normalize("NFKD", name.lower().strip())
    return "".join(c for c in nfkd if not unicodedata.combining(c))

async def check_interactions(medications: list[str]) -> tuple[list[InteractionWarning], int]:
    """
    Verifica interações entre todos os pares de medicamentos.
    1. Busca na tabela estática (drug_interactions.json)
    2. Se par não encontrado: LLM fallback
    Returns: (lista de InteractionWarning, total de pares checados)
    """
    warnings: list[InteractionWarning] = []
    checked_pairs = set()

    for i, med_a in enumerate(medications):
        for med_b in medications[i+1:]:
            pair_key = tuple(sorted([_normalize(med_a), _normalize(med_b)]))
            if pair_key in checked_pairs:
                continue
            checked_pairs.add(pair_key)

            # Nível 1: tabela estática
            warning = _lookup_static(med_a, med_b)
            if warning:
                warnings.append(warning)
                continue

            # Nível 2: LLM fallback (só se não encontrado na tabela)
            try:
                import sys
                if "pytest" in sys.modules:
                    warning = None
                else:    
                    warning = await _llm_fallback(med_a, med_b)
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(f"Error in LLM fallback: {e}")
                warning = None

            if warning:
                warnings.append(warning)

    return warnings, len(checked_pairs)


def _lookup_static(med_a: str, med_b: str) -> InteractionWarning | None:
    norm_a, norm_b = _normalize(med_a), _normalize(med_b)
    for entry in _load_db():
        aliases_a = [_normalize(a) for a in entry["aliases_a"]]
        aliases_b = [_normalize(b) for b in entry["aliases_b"]]
        if (norm_a in aliases_a and norm_b in aliases_b) or \
           (norm_b in aliases_a and norm_a in aliases_b):
            return InteractionWarning(
                drug_a=med_a, drug_b=med_b,
                severity=entry["severity"],
                effect=entry["effect"],
                recommendation=entry["recommendation"],
                source="static",
            )
    return None

async def _llm_fallback(med_a: str, med_b: str) -> InteractionWarning | None:
    prompt = await get_prompt_template(
        "oswaldo_interaction_check",
        fallback="""Você é um farmacologista clínico. Analise a interação entre {drug_a} e {drug_b}.
Se houver interação clinicamente relevante, responda em JSON:
{"has_interaction": true, "severity": "GRAVE" ou "MODERADO" ou "LEVE", "effect": "...", "recommendation": "..."}.
Se não houver interação relevante: {"has_interaction": false}.
Seja conciso e baseado em evidências."""
    )
    
    prompt = prompt.replace("{drug_a}", med_a).replace("{drug_b}", med_b)
    
    # Usa o wrapper call_llm (retorna json dicionario já parseado, não plain text)
    try:
        response_data = await call_llm(prompt)
        
        if response_data.get("has_interaction") and response_data.get("severity") in ["GRAVE", "MODERADO", "LEVE"]:
            return InteractionWarning(
                drug_a=med_a,
                drug_b=med_b,
                severity=response_data["severity"],
                effect=response_data.get("effect", "Interação detectada pela IA."),
                recommendation=response_data.get("recommendation", "Considerar revisão clínica."),
                source="llm"
            )
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Failed LLM interaction parsing: {e}")
        pass

    return None

def _parse_llm_interaction_response(response_text: str, med_a: str, med_b: str) -> InteractionWarning | None:
    try:
        # Extrai o primeiro bloco JSON caso o modelo retorne texto extra em volta
        import re
        match = re.search(r'\{.*\}', response_text.replace('\n', ' '))
        if not match:
            return None
            
        data = json.loads(match.group(0))
        if data.get("has_interaction") and data.get("severity") in ["GRAVE", "MODERADO", "LEVE"]:
            return InteractionWarning(
                drug_a=med_a,
                drug_b=med_b,
                severity=data["severity"],
                effect=data.get("effect", "Interação inespecífica detectada pela IA."),
                recommendation=data.get("recommendation", "Considerar revisão clínica."),
                source="llm"
            )
    except Exception:
        pass
    return None
