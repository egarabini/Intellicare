---
tipo: especificacao-tecnica
demanda: DEM-079
titulo: Florence via Marie RAG
---

# DEM-079 — Especificação Técnica

## Mapa de mudanças

| Arquivo | Tipo | O que muda |
|---------|------|-----------|
| `modules/florence/services.py` | Modificar | `suggest_soap()` — delega ao Marie quando `MARIE_ENABLED=true` |
| `modules/florence/services.py` | Modificar | `_get_florence_timeline_context()` — helper que formata resumo da timeline para o payload RAG |
| `packages/intellicare-core/tests/test_florence_marie.py` | **Novo** | 4+ testes com mock Dify |
| `infra/.env.staging.example` | Modificar | `MARIE_ENABLED=true` para staging (ativar pela primeira vez) |

---

## `modules/florence/services.py` — integração `suggest_soap`

```python
from modules.marie.client import call_marie, is_marie_enabled

def suggest_soap(encounter_id: UUID, ctx) -> FlorenceSuggestion:
    """
    Gera sugestão SOAP.
    MARIE_ENABLED=true  → Marie RAG com contexto longitudinal
    MARIE_ENABLED=false → LLM local com prompt get_active_prompt("florence_soap")
    """
    encounter = get_encounter(encounter_id, ctx)

    def local_fallback():
        prompt = get_active_prompt("florence_soap", fallback=SOAP_PROMPT_FALLBACK)
        return _call_llm(prompt, {"chief_complaint": encounter.chief_complaint})

    if is_marie_enabled():
        context = _get_florence_timeline_context(encounter.patient_id, ctx)
        marie_response = call_marie(
            workflow_slug="florence_soap_rag",
            inputs={
                "chief_complaint": encounter.chief_complaint,
                "patient_history": context,
                "encounter_date": str(encounter.opened_at.date()),
            },
            fallback_fn=local_fallback,
        )
        if marie_response:
            return _parse_marie_soap_response(marie_response)

    return local_fallback()


def _get_florence_timeline_context(patient_id: UUID, ctx, days: int = 180) -> str:
    """
    Formata resumo da timeline para contexto RAG.
    Máximo 3000 chars para não exceder janela de contexto do Dify.
    """
    try:
        timeline = clinical_timeline(patient_id, ctx, limit=20, offset=0)
        lines = []
        for event in timeline.events:
            if event.type == "encounter":
                lines.append(f"[{event.occurred_at.date()}] Consulta: {event.title} | CID: {event.metadata.get('cid', '-')}")
            elif event.type == "prescription":
                drugs = ", ".join(event.metadata.get("drugs", []))
                lines.append(f"[{event.occurred_at.date()}] Prescrição: {drugs}")
            elif event.type == "clinical_note":
                lines.append(f"[{event.occurred_at.date()}] Nota: {event.title[:80]}")
        summary = "\n".join(lines)
        return summary[:3000]  # truncar para janela de contexto
    except Exception:
        return ""  # falha silenciosa — não bloqueia a sugestão
```

---

## Workflow Dify `florence_soap_rag`

Criar no Dify web após `docker compose up` no staging:

```
Input nodes:
  - chief_complaint (string) — motivo da consulta atual
  - patient_history (string) — resumo da timeline (últimos 180 dias)
  - encounter_date (string) — data da consulta

LLM node — prompt:
  "Você é Florence, assistente clínica. Gere uma nota SOAP para:
   Consulta: {{chief_complaint}} em {{encounter_date}}

   Histórico do paciente (últimos 6 meses):
   {{patient_history}}

   Retorne apenas o JSON:
   {\"soap_s\": \"...\", \"soap_o\": \"...\", \"soap_a\": \"...\", \"soap_p\": \"...\"}"

Output node:
  - answer (string) — JSON com campos SOAP
```

---

## Testes — `test_florence_marie.py`

| Teste | Cenário |
|-------|---------|
| `test_florence_marie_disabled_uses_local_llm` | `MARIE_ENABLED=false` → LLM local chamado, Marie não chamado |
| `test_florence_marie_enabled_sends_timeline_context` | `MARIE_ENABLED=true` → payload inclui `patient_history` não vazio |
| `test_florence_marie_timeout_fallback` | Dify timeout → fallback local, sem exception para o clínico |
| `test_florence_timeline_context_truncated` | Timeline com 50 eventos → contexto truncado em 3000 chars |

---

## Staging — ativar `MARIE_ENABLED=true`

Esta DEM é a primeira a rodar com Marie ativo em staging. Após rebuild:

```bash
# Verificar workflow florence_soap_rag publicado no Dify
# Atualizar .env.staging:
MARIE_ENABLED=true

# Reiniciar api
docker compose restart api

# Smoke
curl -s -X POST http://staging:8000/florence/notes/suggest \
  -H "Authorization: Bearer $CLINICO_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"encounter_id": "UUID_DO_ENCOUNTER"}' | jq '{soap_s, soap_a}'
# Resposta deve conter referência ao histórico do paciente em soap_a
```
