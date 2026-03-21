# DEM-067 — Kestra Flows Condicionais

**Sprint:** 2026-04-18
**Dev:** CODEX
**Estimativa:** ~3.5h
**Prioridade:** Média-Alta — os flows atuais são lineares; esta DEM adiciona inteligência de roteamento clínico

---

## Objetivo

Os flows Kestra atuais (DEM-039) executam jornadas lineares: disparo → mensagem WA → mensagem Email → timeout. Não há branching baseado em estado clínico. Esta DEM adiciona:

1. **Branching por canal** — se WhatsApp falhar/expirar, fazer fallback automático para Email
2. **Branching por resposta** — se paciente respondeu "SIM" → confirmar consulta; "NÃO" → reagendar
3. **Retry com backoff** — reenvio após 2h, depois 6h, depois 24h antes de expirar
4. **Flow de urgência clínica** — jornada separada com escalação para clínico se paciente não responde em 1h

---

## Escopo

### 1. Flow: `jornada_com_fallback` (substitui `jornada_basica`)

```yaml
# infra/kestra/flows/jornada_com_fallback.yml

id: jornada_com_fallback
namespace: intellicare

inputs:
  - name: journey_id
    type: STRING
  - name: patient_phone
    type: STRING
  - name: patient_email
    type: STRING
  - name: canal_preferido
    type: STRING
    defaults: whatsapp

tasks:
  - id: tentar_whatsapp
    type: io.kestra.plugin.scripts.python.Script
    # Chama POST /careplanner/dispatch {channel: whatsapp}
    # Retorna: {status: SENT | FAILED, journey_id}

  - id: checar_wa_resultado
    type: io.kestra.core.tasks.flows.Switch
    value: "{{ outputs.tentar_whatsapp.vars.status }}"
    cases:
      SENT:
        - id: aguardar_resposta_wa
          type: io.kestra.core.tasks.flows.Pause
          delay: PT2H
        - id: checar_resposta
          type: io.kestra.core.tasks.flows.Switch
          # ... ver seção 2
      FAILED:
        - id: fallback_email
          type: io.kestra.plugin.scripts.python.Script
          # Chama POST /careplanner/dispatch {channel: email}
```

### 2. Flow: `resposta_confirmacao` (branching por conteúdo)

Webhook Kestra ativado pelo `WhatsAppAdapter` quando paciente responde:

```yaml
  - id: processar_resposta
    type: io.kestra.core.tasks.flows.Switch
    value: "{{ trigger.body.normalized_response }}"  # SIM | NAO | OUTRO
    cases:
      SIM:
        - id: confirmar_consulta
          type: io.kestra.plugin.scripts.python.Script
          # POST /appointments/{id}/confirm
        - id: notificar_clinico_confirmacao
          type: io.kestra.plugin.scripts.python.Script
          # POST /notifications {user_id: clinico_id, title: "Consulta confirmada"}
      NAO:
        - id: iniciar_reagendamento
          type: io.kestra.plugin.scripts.python.Script
          # POST /appointments/{id}/request-reschedule
      OUTRO:
        - id: encaminhar_para_clinico
          type: io.kestra.plugin.scripts.python.Script
          # Notifica clínico para resposta manual via RocketChat
```

**Normalização de resposta no `WhatsAppAdapter`:**
```python
# modules/careplanner/adapters/whatsapp_adapter.py — adicionar:

def normalize_confirmation(text: str) -> str:
    text = text.lower().strip()
    if any(w in text for w in ["sim", "yes", "confirmo", "ok", "1"]):
        return "SIM"
    if any(w in text for w in ["não", "nao", "no", "cancelar", "2"]):
        return "NAO"
    return "OUTRO"
```

### 3. Flow: `retry_com_backoff`

```yaml
id: retry_com_backoff
namespace: intellicare

tasks:
  - id: tentativa_1
    # Disparo inicial

  - id: aguardar_2h
    type: io.kestra.core.tasks.flows.Sleep
    duration: PT2H

  - id: checar_status_1
    type: io.kestra.core.tasks.flows.Switch
    value: "{{ outputs.tentativa_1.vars.journey_status }}"
    cases:
      REPLIED: [id: finalizar_sucesso]
      SENT:
        - id: tentativa_2
          # Reenvio após 2h
        - id: aguardar_6h
          type: io.kestra.core.tasks.flows.Sleep
          duration: PT6H
        - id: checar_status_2
          # ... etc até 24h, depois EXPIRED
```

### 4. Flow: `urgencia_clinica`

Jornada especial para casos urgentes (ex: resultado de exame crítico):

- Dispara WA imediato
- Se não lido em **1h** → notifica clínico via RocketChat
- Se não respondido em **2h** → escala para gestor
- Log de auditoria em `deploy/urgencia_log.txt`

```yaml
id: urgencia_clinica
namespace: intellicare.clinico

inputs:
  - name: urgency_level
    type: STRING   # LOW | MEDIUM | HIGH | CRITICAL
```

### 5. `seed_flows.py` atualizado

```python
# infra/kestra/seed_flows.py — adicionar os 3 flows novos

FLOWS = [
    "flows/jornada_basica.yml",          # mantém para compatibilidade
    "flows/jornada_com_fallback.yml",    # novo
    "flows/resposta_confirmacao.yml",    # novo
    "flows/retry_com_backoff.yml",       # novo
    "flows/urgencia_clinica.yml",        # novo
    "flows/jornada_whatsapp.yml",
    "flows/jornada_email.yml",
    "flows/jornada_sms.yml",
]
```

### 6. `trigger_flow()` — parâmetro `flow_id` dinâmico

```python
# modules/careplanner/integrations.py — atualizar trigger_flow

async def trigger_flow(journey_id: str, flow_id: str = "jornada_com_fallback", **kwargs):
    # flow_id agora configurável por journey template
```

---

## Testes esperados (mínimo 5)

```python
# tests/test_kestra_flows.py

test_fallback_email_on_wa_failure()         # WA retorna FAILED → email disparado
test_confirmation_sim_confirms_appointment() # resposta "sim" → consulta confirmada
test_confirmation_nao_requests_reschedule() # resposta "não" → reagendamento solicitado
test_retry_backoff_3_attempts()             # 3 tentativas com intervalos crescentes
test_urgencia_escalates_after_1h()          # sem leitura em 1h → notificação clínico
test_normalize_confirmation_variants()      # "Sim", "SIM", "ok", "1" → "SIM"
```

---

## Arquivos a criar/modificar

```
infra/kestra/flows/
├── jornada_com_fallback.yml       (novo)
├── resposta_confirmacao.yml       (novo)
├── retry_com_backoff.yml          (novo)
└── urgencia_clinica.yml           (novo)
infra/kestra/
└── seed_flows.py                  (atualizar lista de flows)
modules/careplanner/
├── adapters/whatsapp_adapter.py   (adicionar normalize_confirmation)
└── integrations.py                (flow_id dinâmico em trigger_flow)
```

---

## Gotcha importante

O Kestra 0.20 usa `io.kestra.core.tasks.flows.Switch` com campo `value` (string interpolada) e `cases` (map string → lista de tasks). **Não** usar `if/else` — não é suportado nativamente. Para condições booleanas simples, usar Switch com `"true"/"false"` como cases.

---

## Critério de aceite

1. `seed_flows.py` sobe os 4 flows novos no Kestra sem erros
2. Flow `jornada_com_fallback` ao receber WA FAILED dispara Email automaticamente
3. Webhook de resposta normaliza "sim"/"confirmo"/"ok" → `SIM` corretamente
4. 5/6 testes passando (urgência pode ser mockada em CI)
5. `trigger_flow()` aceita `flow_id` como parâmetro sem breaking change
