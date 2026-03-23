---
tipo: especificacao-tecnica
demanda: DEM-077
titulo: Oswaldo — Interação Medicamentosa
---

# DEM-077 — Especificação Técnica

## Mapa de mudanças

| Arquivo | Tipo | O que muda |
|---------|------|-----------|
| `data/drug_interactions.json` | **Novo** | Tabela estática de ~150 pares de interações |
| `modules/oswaldo/interactions.py` | **Novo** | `check_interactions()`, `_lookup_static()`, `_llm_fallback()` |
| `modules/oswaldo/schemas.py` | Modificar | `InteractionWarning`, `CheckInteractionsRequest`, `CheckInteractionsResponse` |
| `modules/oswaldo/routes.py` | Modificar | `POST /oswaldo/check-interactions` |
| `frontend/ClinicoUI/src/components/InteractionWarningBanner.tsx` | **Novo** | Banner com severidade, descrição e botão "Entendido" |
| `frontend/ClinicoUI/src/pages/OswaldoPrescriptionEditor.tsx` | Modificar | Chamar check-interactions ao adicionar/remover medicamento |
| `packages/intellicare-core/tests/test_oswaldo_interactions.py` | **Novo** | 5+ testes |

---

## Estrutura `drug_interactions.json`

```json
[
  {
    "drug_a": "varfarina",
    "drug_b": "ácido acetilsalicílico",
    "aliases_a": ["varfarina", "warfarina", "coumadin"],
    "aliases_b": ["aas", "aspirina", "ácido acetilsalicílico", "asa"],
    "severity": "GRAVE",
    "effect": "Risco hemorrágico aumentado — potencialização do efeito anticoagulante",
    "recommendation": "Evitar combinação ou monitorar INR rigorosamente"
  },
  {
    "drug_a": "fluoxetina",
    "drug_b": "tramadol",
    "aliases_a": ["fluoxetina", "prozac", "daforin"],
    "aliases_b": ["tramadol", "tramal"],
    "severity": "GRAVE",
    "effect": "Síndrome serotoninérgica — agitação, hipertermia, rigidez muscular",
    "recommendation": "Contraindicado — substituir um dos agentes"
  }
  // ... ~148 pares adicionais
]
```

**Matching normalizado:** comparação em lowercase sem acentos, usando aliases para cobrir nomes genéricos e comerciais.

---

## `modules/oswaldo/interactions.py`

```python
import json
import unicodedata
from pathlib import Path
from intellicare_core.shared.llm import get_active_prompt, _call_llm

_INTERACTIONS_DB = None

def _load_db() -> list:
    global _INTERACTIONS_DB
    if _INTERACTIONS_DB is None:
        path = Path(__file__).parent.parent.parent / "data/drug_interactions.json"
        _INTERACTIONS_DB = json.loads(path.read_text())
    return _INTERACTIONS_DB

def _normalize(name: str) -> str:
    """Lowercase + remove acentos para matching tolerante."""
    nfkd = unicodedata.normalize("NFKD", name.lower())
    return "".join(c for c in nfkd if not unicodedata.combining(c))

def check_interactions(medications: list[str]) -> list[InteractionWarning]:
    """
    Verifica interações entre todos os pares de medicamentos.
    1. Busca na tabela estática (drug_interactions.json)
    2. Se par não encontrado: LLM fallback
    Returns lista de InteractionWarning (pode ser vazia).
    """
    warnings = []
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
            warning = _llm_fallback(med_a, med_b)
            if warning:
                warnings.append(warning)

    return warnings

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

def _llm_fallback(med_a: str, med_b: str) -> InteractionWarning | None:
    prompt = get_active_prompt(
        "oswaldo_interaction_check",
        fallback=INTERACTION_PROMPT_FALLBACK,
    )
    response = _call_llm(prompt, {"drug_a": med_a, "drug_b": med_b})
    # Parser do JSON retornado pelo LLM
    # Se LLM não identifica interação relevante, retorna None
    return _parse_llm_interaction_response(response, med_a, med_b)
```

---

## Schemas

```python
class InteractionWarning(BaseModel):
    drug_a: str
    drug_b: str
    severity: Literal["GRAVE", "MODERADO", "LEVE"]
    effect: str
    recommendation: str
    source: Literal["static", "llm"]

class CheckInteractionsRequest(BaseModel):
    medications: list[str]  # lista de nomes dos medicamentos

class CheckInteractionsResponse(BaseModel):
    warnings: list[InteractionWarning]
    checked_pairs: int
```

---

## Endpoint

```
POST /oswaldo/check-interactions
Authorization: Bearer {clinico_token}
Body: { "medications": ["varfarina", "AAS", "atenolol"] }

Response 200:
{
  "warnings": [
    {
      "drug_a": "varfarina",
      "drug_b": "AAS",
      "severity": "GRAVE",
      "effect": "Risco hemorrágico aumentado...",
      "recommendation": "Evitar combinação ou monitorar INR",
      "source": "static"
    }
  ],
  "checked_pairs": 3
}
```

---

## Frontend — `InteractionWarningBanner.tsx`

```tsx
// Props
interface Props {
  warnings: InteractionWarning[]
  onDismiss: () => void
}

// Cores por severidade
const severityColor = { GRAVE: "red", MODERADO: "yellow", LEVE: "blue" }

// Renderiza um Alert Mantine por warning
// Botão "Entendido — manter prescrição" chama onDismiss()
```

**Integração em `OswaldoPrescriptionEditor.tsx`:**
- `useEffect` dispara `POST /oswaldo/check-interactions` sempre que `medications[]` muda
- Debounce de 500ms para não spammar chamadas ao adicionar vários medicamentos de uma vez
- Estado `warnings: InteractionWarning[]` — se vazio, banner não renderiza
- `onDismiss` limpa o estado `warnings`

---

## Novo slug de prompt para LLM fallback

Adicionar seed em migration futura (ou inserção direta):
```sql
INSERT INTO platform.prompt_templates (slug, version, content, is_active, description)
VALUES (
  'oswaldo_interaction_check', 1,
  'Você é um farmacologista clínico. Analise a interação entre {{drug_a}} e {{drug_b}}.
   Se houver interação clinicamente relevante, responda em JSON:
   {"has_interaction": true, "severity": "GRAVE|MODERADO|LEVE", "effect": "...", "recommendation": "..."}.
   Se não houver interação relevante: {"has_interaction": false}.
   Seja conciso e baseado em evidências.',
  TRUE,
  'Verificação de interação medicamentosa via LLM'
) ON CONFLICT (slug, version) DO NOTHING;
```
