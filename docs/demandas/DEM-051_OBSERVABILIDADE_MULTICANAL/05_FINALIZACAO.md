# DEM-051 Observabilidade Multicanal — Finalização

## Status: ✅ CONCLUÍDA

- **Commit:** `2fa8949` (`2fa894924be98cc42be3368b53598334722e3089`)
- **Mensagem:** `feat(careplanner): DEM-051 healthcheck adapters + label channel no Grafana`
- **Entregador:** DEV-2
- **Data:** 2026-03-21

---

## O que foi entregue

### `GET /health/adapters`

Endpoint público de healthcheck verificando conectividade dos 4 adaptadores de canal:

| Adapter | Verificação |
|---|---|
| RocketChat | HTTP GET no endpoint base RC |
| Evolution API | HTTP GET `/instance/fetchInstances` |
| Listmonk | HTTP GET `/api/health` |
| Jasmin | TCP/HTTP no host configurado |

Resposta: JSON com status por canal (`ok` / `error`) + HTTP 200 sempre (degradado, não fatal).

### Prometheus — label `channel`

`careplanner_dispatch_total` passa a registrar label `channel` com valores `ROCKETCHAT`, `WHATSAPP`, `EMAIL`, `SMS`.

Permite queries como:
```promql
sum by (channel) (rate(careplanner_dispatch_total[5m]))
```

### Grafana — 4 painéis adicionados ao dashboard `careplanner-overview`

| Painel | Query base |
|---|---|
| Disparos por canal (stacked) | `sum by (channel)(rate(careplanner_dispatch_total[5m]))` |
| Taxa de falha por canal | `...{status="FAILED"} / ...{status=~".+"}` |
| Latência p95 DISPATCHED→SENT | `histogram_quantile(0.95, ...)` filtrado por canal |
| Status adapters | valor booleano de `/health/adapters` via Blackbox ou scrape direto |

---

## Fora do escopo desta DEM

- Alertas Grafana por canal (pode ser DEM-INF futura ou extensão da DEM-028).
- Histórico de disponibilidade dos adapters (série temporal, não só snapshot).
- Dashboard separado para canal SMS/Email (uso real ainda baixo).

---

## Critérios de aceite — verificação final

- [x] `GET /health/adapters` retorna JSON com status de RC, Evolution, Listmonk e Jasmin
- [x] Label `channel` presente em `careplanner_dispatch_total`
- [x] 4 painéis Grafana adicionados ao `careplanner-overview`
- [x] Testes cobrindo endpoint healthcheck (200 + estrutura de resposta)
