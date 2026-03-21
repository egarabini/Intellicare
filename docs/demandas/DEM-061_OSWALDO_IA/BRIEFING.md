# DEM-061 — Oswaldo IA: Sugestão de CID-10 e Posologia via LLM

> **Dev:** DEV-2
> **Estimativa:** ~3.5h
> **Dependência:** DEM-058 (Oswaldo base), DEM-057 (Florence IA — padrão LLM já estabelecido)
> **Executor Matrix:** `oswaldo_suggest()` → **Hybrid** | `_call_llm()` → **Agent**

---

## Contexto

Oswaldo base (DEM-058) entregou busca textual de CID-10 e CRUD de prescrições.
Esta DEM adiciona a camada de IA seguindo **exatamente o mesmo padrão** de DEM-057
(Florence IA): endpoint de sugestão, `_call_llm()` OpenAI-compatible, fallback
determinístico, variáveis de ambiente opcionais.

O clínico descreve a queixa principal e o contexto do encontro. Oswaldo sugere:
1. CID-10 mais provável (código + descrição)
2. Itens de prescrição sugeridos (medicamento, posologia, duração)

Nunca auto-salva. Clínico revisa antes de confirmar.

---

## Fase A — Backend

### STEP-001 — Contracts

`modules/oswaldo/contracts.py` — adicionar:

```python
class OswaldoSuggestRequest(BaseModel):
    encounter_id: int
    patient_id: int
    chief_complaint: str
    recent_diagnoses: list[str] | None = None   # CID-10 de encontros anteriores
    current_medications: list[str] | None = None

class OswaldoSuggestion(BaseModel):
    cid10_code: str
    cid10_desc: str
    prescription_items: list[PrescriptionItem]
    model: str
    confidence: str   # "high" | "medium" | "low"
```

### STEP-002 — Service de sugestão

`modules/oswaldo/services.py` — seguir estrutura idêntica ao `modules/florence/services.py`:

```python
OSWALDO_PROMPT = """
Você é um assistente clínico. Com base nas informações abaixo, sugira:
1. O CID-10 mais provável (código e descrição curta)
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

async def suggest(ctx, req: OswaldoSuggestRequest) -> OswaldoSuggestion:
    prompt = OSWALDO_PROMPT.format(
        chief_complaint=req.chief_complaint,
        recent_diagnoses=", ".join(req.recent_diagnoses or []) or "nenhum",
        current_medications=", ".join(req.current_medications or []) or "nenhum",
    )
    try:
        result = await _call_llm(ctx, prompt)
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
```

### STEP-003 — `_call_llm` e fallback

Reutilizar `_call_llm()` de `modules/florence/services.py` ou extrair para
`modules/shared/llm.py` se quiser evitar duplicação. Fallback:

```python
def _rule_based_suggestion(req: OswaldoSuggestRequest) -> dict:
    return {
        "cid10_code": "Z00",
        "cid10_desc": "Consulta de rotina (preencher manualmente)",
        "items": [],
        "model": "rule-based",
    }
```

### STEP-004 — Endpoint

`modules/oswaldo/api/routes.py`:

```python
@router.post("/suggest", response_model=OswaldoSuggestion)
async def suggest(
    req: OswaldoSuggestRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    _: UserClaims = Depends(require_roles(["CLINICO"])),
):
    return await oswaldo_service.suggest(ctx, req)
```

### STEP-005 — Variáveis de ambiente

Reutilizar as mesmas vars de Florence — Oswaldo usa o mesmo LLM:

```env
# Já existem de DEM-057 — não duplicar
FLORENCE_LLM_URL=
FLORENCE_LLM_API_KEY=
FLORENCE_LLM_MODEL=gpt-4o-mini
```

> Se quiser separação de modelos no futuro: `OSWALDO_LLM_MODEL`. Por ora reutilizar.

---

## Fase B — Frontend ClinicoUI

### STEP-006 — Botão "Sugerir com IA" no OswaldoPrescriptionEditor

`ClinicoUI/components/OswaldoPrescriptionEditor.tsx`:

```tsx
const [chiefComplaint, setChiefComplaint] = useState('')
const [loading, setLoading] = useState(false)

const handleSuggest = async () => {
  setLoading(true)
  try {
    const suggestion = await api.post('/oswaldo/suggest', {
      encounter_id: encounterId,
      patient_id: patientId,
      chief_complaint: chiefComplaint,
    })
    // Preenche CID-10 e itens — clínico edita antes de salvar
    onCID10Select({ code: suggestion.cid10_code, description: suggestion.cid10_desc })
    setItems(suggestion.prescription_items)
    if (suggestion.confidence === 'low') showLowConfidenceBadge()
  } finally {
    setLoading(false)
  }
}

// UI — campo motivo + botão (mesma UX do Florence)
<TextInput
  label="Motivo da consulta"
  value={chiefComplaint}
  onChange={(e) => setChiefComplaint(e.target.value)}
/>
<Button
  leftSection={<IconSparkles size={14} />}
  variant="light"
  color="teal"
  loading={loading}
  disabled={!chiefComplaint}
  onClick={handleSuggest}
>
  Sugerir CID-10 e prescrição com IA
</Button>
```

---

## Fase C — Testes

### STEP-007

`packages/intellicare-core/tests/test_oswaldo_ia.py`:

```python
async def test_suggest_rule_based(async_client, monkeypatch):
    monkeypatch.delenv("FLORENCE_LLM_URL", raising=False)
    resp = await async_client.post("/oswaldo/suggest", json={
        "encounter_id": 1,
        "patient_id": 1,
        "chief_complaint": "Dor de garganta há 3 dias",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["model"] == "rule-based"
    assert data["confidence"] == "low"
    assert "cid10_code" in data

async def test_suggest_missing_complaint(async_client):
    resp = await async_client.post("/oswaldo/suggest", json={
        "encounter_id": 1,
        "patient_id": 1,
    })
    assert resp.status_code == 422
```

---

## Critérios de Aceite

- [ ] `POST /oswaldo/suggest` retorna `OswaldoSuggestion` com CID-10 + itens
- [ ] Fallback rule-based funciona sem LLM configurado
- [ ] Botão "Sugerir com IA" visível no `OswaldoPrescriptionEditor`
- [ ] CID-10 e itens preenchidos pela IA são editáveis antes de salvar
- [ ] Badge `confidence: low` quando fallback
- [ ] 2 testes passando

## Executor Matrix

| Componente | Categoria | Justificativa |
|---|---|---|
| `oswaldo_service.suggest()` | Hybrid | Propõe CID-10 e prescrição; clínico decide confirmar |
| `_call_llm()` (via florence ou shared) | Agent | Chama API externa com custo — opt-in via env |
| `_rule_based_suggestion()` | Worker | Determinístico, sem efeito externo |
