# DEM-057 — Florence IA: Sugestão Automática de Campos SOAP

> **Dev:** DEV-2
> **Estimativa:** ~4h
> **Dependência:** DEM-055 (Florence base), DEM-020 (EncounterView com dados do encontro)
> **Executor Matrix:** `florence_suggest()` → **Hybrid** (sugere, clínico decide salvar)

---

## Contexto

Florence base (DEM-055) entregou a estrutura de dados e a UI de edição SOAP/FREE.
Esta DEM adiciona a camada de IA: ao abrir um encontro, o clínico pode solicitar
sugestões automáticas para os 4 campos SOAP com base no contexto clínico disponível
(motivo da consulta, histórico recente, CID-10 do agendamento vinculado).

A classificação na Executor Matrix é **Hybrid** — a IA propõe, o clínico revisa e
decide salvar. Nunca auto-salva.

---

## Fase A — Backend

### STEP-001 — Endpoint de sugestão

`modules/florence/api/routes.py` — novo endpoint:

```python
@router.post("/notes/suggest", response_model=SOAPSuggestion)
async def suggest_soap(
    req: SuggestRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    _: UserClaims = Depends(require_roles(["CLINICO"])),
):
    return await florence_service.suggest_soap(ctx, req)
```

### STEP-002 — Contracts

`modules/florence/contracts.py` — adicionar:

```python
class SuggestRequest(BaseModel):
    encounter_id: int
    patient_id: int
    chief_complaint: str           # motivo da consulta — preenchido pelo clínico
    appointment_reason: str | None = None   # do agendamento vinculado, se houver
    recent_notes: list[str] | None = None   # últimas 3 notas do paciente

class SOAPSuggestion(BaseModel):
    soap_s: str
    soap_o: str
    soap_a: str
    soap_p: str
    model: str          # identifica qual LLM/regra gerou a sugestão
    confidence: str     # "high" | "medium" | "low"
```

### STEP-003 — Service de sugestão

`modules/florence/services.py`:

```python
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

    # Tentar LLM configurado; fallback para regras determinísticas
    try:
        result = await _call_llm(ctx, prompt)
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
```

### STEP-004 — `_call_llm` e fallback

```python
async def _call_llm(ctx: TenantContext, prompt: str) -> dict:
    """
    Chama o LLM configurado via FLORENCE_LLM_URL e FLORENCE_LLM_API_KEY.
    Compatível com qualquer endpoint OpenAI-compatible (Ollama, OpenAI, Groq, etc).
    """
    import httpx, os, json

    url = os.getenv("FLORENCE_LLM_URL", "")
    api_key = os.getenv("FLORENCE_LLM_API_KEY", "")

    if not url:
        raise RuntimeError("FLORENCE_LLM_URL not configured")

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            url,
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": os.getenv("FLORENCE_LLM_MODEL", "gpt-4o-mini"),
                "messages": [{"role": "user", "content": prompt}],
                "response_format": {"type": "json_object"},
                "temperature": 0.3,
            },
        )
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]
        data = json.loads(content)
        data["model"] = os.getenv("FLORENCE_LLM_MODEL", "gpt-4o-mini")
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
```

### STEP-005 — Variáveis de ambiente

Adicionar ao `.env.example` e `.env.staging.example`:

```env
# Florence IA — opcional (fallback rule-based se ausente)
FLORENCE_LLM_URL=
FLORENCE_LLM_API_KEY=
FLORENCE_LLM_MODEL=gpt-4o-mini
```

> **Nota:** sem LLM configurado o endpoint funciona normalmente via fallback
> determinístico. Staging pode testar sem custos de API.

---

## Fase B — Frontend ClinicoUI

### STEP-006 — Botão "Sugerir SOAP" no FlorenceNoteEditor

`ClinicoUI/components/FlorenceNoteEditor.tsx`:

```tsx
const [loading, setLoading] = useState(false)
const [chiefComplaint, setChiefComplaint] = useState('')

const handleSuggest = async () => {
  setLoading(true)
  try {
    const suggestion = await api.post('/florence/notes/suggest', {
      encounter_id: encounterId,
      patient_id: patientId,
      chief_complaint: chiefComplaint,
    })
    // Preenche os campos — clínico pode editar antes de salvar
    setFields({
      s: suggestion.soap_s,
      o: suggestion.soap_o,
      a: suggestion.soap_a,
      p: suggestion.soap_p,
      free: fields.free,
    })
  } finally {
    setLoading(false)
  }
}

// UI — só aparece quando noteType === 'SOAP'
{noteType === 'SOAP' && (
  <>
    <TextInput
      label="Motivo da consulta"
      placeholder="Descreva brevemente o motivo"
      value={chiefComplaint}
      onChange={(e) => setChiefComplaint(e.target.value)}
    />
    <Button
      leftSection={<IconSparkles size={14} />}
      variant="light"
      color="violet"
      loading={loading}
      disabled={!chiefComplaint}
      onClick={handleSuggest}
    >
      Sugerir SOAP com IA
    </Button>
    {suggestion?.confidence === 'low' && (
      <Text size="xs" c="dimmed">
        Sugestão gerada por regras (LLM não configurado) — revise com atenção.
      </Text>
    )}
  </>
)}
```

---

## Fase C — Testes

### STEP-007 — Testes Python

`packages/intellicare-core/tests/test_florence_ia.py`:

```python
async def test_suggest_soap_rule_based(async_client, monkeypatch):
    """Sem LLM configurado, retorna sugestão de regras sem erro."""
    monkeypatch.delenv("FLORENCE_LLM_URL", raising=False)
    resp = await async_client.post("/florence/notes/suggest", json={
        "encounter_id": 1,
        "patient_id": 1,
        "chief_complaint": "Dor de cabeça há 2 dias",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["soap_s"] == "Dor de cabeça há 2 dias"
    assert data["model"] == "rule-based"
    assert data["confidence"] == "low"

async def test_suggest_soap_missing_complaint(async_client):
    """Campo chief_complaint obrigatório."""
    resp = await async_client.post("/florence/notes/suggest", json={
        "encounter_id": 1,
        "patient_id": 1,
    })
    assert resp.status_code == 422
```

---

## Critérios de Aceite

- [ ] `POST /florence/notes/suggest` retorna `SOAPSuggestion` com os 4 campos
- [ ] Fallback rule-based funciona sem `FLORENCE_LLM_URL` configurada
- [ ] Botão "Sugerir SOAP com IA" visível no `FlorenceNoteEditor` quando modo SOAP
- [ ] Campos preenchidos pela IA são editáveis antes de salvar (nunca auto-salva)
- [ ] Badge de `confidence: low` exibido quando fallback rule-based
- [ ] 2 testes passando (rule-based + validação de campo obrigatório)

---

## Executor Matrix

| Componente | Categoria | Justificativa |
|---|---|---|
| `florence_service.suggest_soap()` | Hybrid | Propõe texto; clínico decide salvar — nunca persiste automaticamente |
| `_call_llm()` | Agent | Chama API externa com custo por token — requer `FLORENCE_LLM_URL` configurada explicitamente |
| `_rule_based_suggestion()` | Worker | Determinístico, sem efeito externo, sem custo |
