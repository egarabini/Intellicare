---
tipo: especificacao-tecnica
demanda: DEM-067
titulo: Kestra Flows Condicionais
---

# DEM-067 — Especificação Técnica

## Mapa de mudanças

| Arquivo | Tipo | O que muda |
|---------|------|-----------|
| `infra/kestra/flows/jornada_com_fallback.yml` | **Novo** | WA → fallback Email se FAILED |
| `infra/kestra/flows/resposta_confirmacao.yml` | **Novo** | Branching SIM/NÃO/OUTRO |
| `infra/kestra/flows/retry_com_backoff.yml` | **Novo** | Reenvio 2h → 6h → 24h → EXPIRED |
| `infra/kestra/flows/urgencia_clinica.yml` | **Novo** | Escala clínico em 1h, gestor em 2h |
| `infra/kestra/seed_flows.py` | Modificar | Adicionar 4 flows novos à lista |
| `modules/careplanner/adapters/whatsapp_adapter.py` | Modificar | `normalize_confirmation()` |
| `modules/careplanner/integrations.py` | Modificar | `trigger_flow()` com `flow_id` dinâmico |
| `tests/test_kestra_flows.py` | **Novo** | 6 testes |

---

## Flows novos — estrutura resumida

### `jornada_com_fallback.yml`

```
inputs: journey_id, patient_phone, patient_email, canal_preferido (default: whatsapp)
tasks:
  tentar_whatsapp → Switch(status):
    SENT  → aguardar_resposta_wa (Pause PT2H)
    FAILED → fallback_email → POST /careplanner/dispatch {channel: email}
```

### `resposta_confirmacao.yml`

```
trigger: webhook (ativado pelo WhatsAppAdapter ao receber mensagem)
tasks:
  processar_resposta → Switch(normalized_response):
    SIM   → confirmar_consulta + notificar_clinico_confirmacao
    NAO   → iniciar_reagendamento
    OUTRO → encaminhar_para_clinico (RocketChat manual)
```

### `retry_com_backoff.yml`

```
tentativa_1 → Sleep(PT2H) → checar_status:
  REPLIED → finalizar_sucesso
  SENT    → tentativa_2 → Sleep(PT6H) → checar_status:
    REPLIED → finalizar_sucesso
    SENT    → tentativa_3 → Sleep(PT18H) → checar_status:
      REPLIED → finalizar_sucesso
      * → marcar_EXPIRED
```

### `urgencia_clinica.yml`

```
inputs: journey_id, patient_phone, urgency_level (LOW|MEDIUM|HIGH|CRITICAL)
tasks:
  disparo_wa_imediato
  → Sleep(PT1H)
  → checar_leitura:
    SEEN    → aguardar_resposta
    NOT_SEEN → notificar_clinico_rocketchat
  → Sleep(PT1H)
  → checar_resposta:
    REPLIED  → fechar_urgencia
    NO_REPLY → escalar_gestor + log_auditoria
```

---

## `normalize_confirmation()` — `whatsapp_adapter.py`

```python
def normalize_confirmation(text: str) -> str:
    text = text.lower().strip()
    positivos = {"sim", "yes", "confirmo", "confirmado", "ok", "claro", "1", "s"}
    negativos = {"não", "nao", "no", "cancelar", "cancelo", "recuso", "2", "n"}
    if any(w in text for w in positivos):
        return "SIM"
    if any(w in text for w in negativos):
        return "NAO"
    return "OUTRO"
```

---

## `trigger_flow()` — assinatura atualizada

```python
# modules/careplanner/integrations.py

async def trigger_flow(
    journey_id: str,
    flow_id: str = "jornada_com_fallback",   # ← novo parâmetro com default
    **kwargs
) -> str:
    """
    Retorna execution_id do Kestra.
    flow_id pode ser qualquer flow registrado em infra/kestra/flows/.
    Chamadas existentes sem flow_id continuam funcionando (backward compatible).
    """
```

---

## Gotcha Kestra 0.20 — Switch syntax

```yaml
# ✅ Correto em Kestra 0.20
- id: checar_canal
  type: io.kestra.core.tasks.flows.Switch
  value: "{{ outputs.tentar_whatsapp.vars.status }}"
  cases:
    SENT:
      - id: proxima_task
        ...
    FAILED:
      - id: fallback
        ...

# ❌ Errado — if/else não existe nativamente
```

Para condições booleanas: usar `Switch` com cases `"true"` / `"false"`.

---

## `seed_flows.py` — lista atualizada

```python
FLOWS = [
    "flows/jornada_basica.yml",           # mantido para compatibilidade
    "flows/jornada_com_fallback.yml",     # novo — default a partir de DEM-067
    "flows/resposta_confirmacao.yml",     # novo
    "flows/retry_com_backoff.yml",        # novo
    "flows/urgencia_clinica.yml",         # novo
    "flows/jornada_whatsapp.yml",
    "flows/jornada_email.yml",
    "flows/jornada_sms.yml",
]
```
