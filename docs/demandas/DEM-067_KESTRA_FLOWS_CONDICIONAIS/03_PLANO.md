---
tipo: plano-execucao
demanda: DEM-067
titulo: Kestra Flows Condicionais
status: em-execucao
dev: CODEX
criado: 2026-03-21
---

# DEM-067 — Plano de Execução

## Estimativa

Tempo estimado: ~3.5h | Complexidade: média

O núcleo é a sintaxe Switch do Kestra 0.20 — uma vez dominada, os 4 flows são variações do mesmo padrão. A maior armadilha é o Kestra Switch syntax (ver Gotcha em 02_TECNICA.md).

---

## Ordem de execução

### Bloco 1 — Backend Python (1h)
1. Atualizar `modules/careplanner/adapters/whatsapp_adapter.py`
   - Adicionar `normalize_confirmation()`
   - Testar variantes: "sim", "Sim", "SIM", "confirmo", "ok", "1"
2. Atualizar `modules/careplanner/integrations.py`
   - Adicionar parâmetro `flow_id` com default backward-compatible
3. Verificar que `POST /journeys/trigger` passa `flow_id` ao `trigger_flow()`

### Bloco 2 — Flows YAML (1.5h)
4. Criar `jornada_com_fallback.yml` — começar por este (mais simples)
5. Criar `resposta_confirmacao.yml` — webhook trigger + Switch 3 cases
6. Criar `retry_com_backoff.yml` — 3 níveis de Sleep+Switch encadeados
7. Criar `urgencia_clinica.yml` — dois checkpoints temporais + escala
8. Atualizar `seed_flows.py` com os 4 novos flows

### Bloco 3 — Testes (1h)
9. Criar `tests/test_kestra_flows.py`:
   - `test_normalize_confirmation_variants()`
   - `test_trigger_flow_accepts_flow_id()`
   - `test_fallback_email_on_wa_failure()` (mock dispatcher)
   - `test_confirmation_sim_confirms_appointment()` (mock HTTP)
   - `test_confirmation_nao_requests_reschedule()` (mock HTTP)
   - `test_retry_backoff_3_attempts()` (mock Sleep + status checks)
10. Rodar — garantir 0 regressões nos flows existentes

---

## Gotcha — Kestra Pause em testes

`io.kestra.core.tasks.flows.Pause` e `Sleep` não podem ser testados em tempo real. Mockar o check de status diretamente:

```python
# No teste, mockar a função que lê o status da jornada
with patch("modules.careplanner.integrations.get_journey_status", return_value="SENT"):
    result = await check_retry_needed(journey_id)
    assert result == "RETRY"
```

---

## Gotcha — `jornada_basica` deve permanecer

**Não remover** `jornada_basica.yml`. Jornadas ativas no staging que referenciam esse flow_id quebrarias. O novo default é `jornada_com_fallback` apenas para novas jornadas criadas após DEM-067.

---

## Entrega

Commit com mensagem:
```
feat(kestra): flows condicionais — fallback canal, branching resposta, retry backoff, urgência clínica
```
Hash → enviar para o ARQUITETO fechar DEM-067.
