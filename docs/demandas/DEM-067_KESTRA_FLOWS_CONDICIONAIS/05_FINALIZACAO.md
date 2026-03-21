# DEM-067 — Kestra Flows Condicionais — FINALIZAÇÃO

**Data de entrega:** 2026-03-21
**Dev responsável:** CODEX
**Commit final:** `5b7e1a42`
**Mensagem:** `feat(kestra): flows condicionais - fallback canal, branching resposta, retry backoff, urgencia clinica`
**Sprint:** 2026-04-18

---

## Resumo da entrega

4 flows Kestra condicionais implementados sobre a estrutura real do projeto. As jornadas CarePlanner deixaram de ser lineares e passaram a reagir ao comportamento do paciente e à disponibilidade dos canais.

---

## O que foi entregue

| Arquivo | Descrição |
|---------|-----------|
| `infra/kestra/flows/careplanner_jornada_com_fallback.yml` | WA FAILED → fallback automático Email |
| `infra/kestra/flows/careplanner_resposta_confirmacao.yml` | Branching SIM/NÃO/OUTRO via webhook |
| `infra/kestra/flows/careplanner_retry_com_backoff.yml` | Reenvio 2h → 6h → 24h → EXPIRED |
| `infra/kestra/flows/careplanner_urgencia_clinica.yml` | Escala clínico em 1h, gestor em 2h |
| `modules/careplanner/adapters/whatsapp.py` | `normalize_confirmation()` adicionado |
| `modules/careplanner/services.py` | Inbound WA agora resume Kestra com `content` + `normalized_response` |
| `modules/careplanner/routes.py` | Webhook e flow default atualizados |
| `infra/kestra/seed_flows.py` | 4 flows novos adicionados à lista de seed |

---

## Observação técnica relevante

> `trigger_flow()` já aceitava `flow_id` dinâmico antes desta DEM.

O ajuste necessário foi apenas trocar o **default do request** para `careplanner_jornada_com_fallback`. Isso preserva backward compatibility total — jornadas ativas que não especificam `flow_id` passam automaticamente a usar o flow com fallback de canal.

---

## Validação

```
pytest packages/intellicare-core/tests/test_careplanner_phase_e.py \
       packages/intellicare-core/tests/test_careplanner_phase_h.py \
       packages/intellicare-core/tests/test_careplanner_multicanal.py \
       packages/intellicare-core/tests/test_kestra_flows_condicionais.py -q

Resultado: 24 passed
```

Cobertura: phases E (CarePlanner base), H (WhatsApp), multicanal e os 4 flows condicionais novos — sem nenhuma regressão nos flows anteriores.

---

## Impacto em DEM-068

DEV-3/4 deve validar no staging:
- `seed_flows.py` sobe os 4 flows novos sem erros
- Kestra lista `careplanner_jornada_com_fallback` entre os flows ativos
- `POST /journeys/trigger` com `flow_id: careplanner_jornada_com_fallback` retorna `execution_id`
