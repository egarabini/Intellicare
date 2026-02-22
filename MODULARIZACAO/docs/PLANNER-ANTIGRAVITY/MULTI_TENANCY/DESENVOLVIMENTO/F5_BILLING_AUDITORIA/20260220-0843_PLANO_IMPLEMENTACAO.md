# F5 — Plano de Implementação: Billing + Auditoria Global

> **DEV Atribuído:** DEV 5  
> **Depende de:** F1 (intellicare-admin deve existir como base)  
> **Pode rodar em paralelo com:** F2, F3, F4

---

## Ordem de Execução

| # | Task | Estimativa | Depende de |
|---|---|---|---|
| 1 | Modelos ORM (UsageMetric, Alert) + Migrations | 1 dia | F1 completo |
| 2 | UsageMetricsMiddleware (emissão de métricas) | 1 dia | Task 1 |
| 3 | UsageCollector (consumer Redis) | 1.5 dias | Task 1 |
| 4 | BillingService (cálculo + excedentes) | 2 dias | Tasks 1, 3 |
| 5 | AlertService (verificação de limites) | 1 dia | Tasks 1, 3 |
| 6 | API Routes (billing, usage, alerts) | 1 dia | Tasks 4, 5 |
| 7 | Scheduler (APScheduler/Celery) | 0.5 dia | Tasks 4, 5 |
| 8 | Dashboard financeiro (endpoint + dados) | 0.5 dia | Task 6 |
| 9 | Exportação CSV/PDF | 0.5 dia | Task 6 |
| 10 | Testes | 1.5 dias | Todas |

**Total: 10 dias**

---

## Checklist de Entrega

- [ ] Métricas de uso coletadas por tenant/dia
- [ ] Billing mensal gerado com plano + excedentes
- [ ] Suspensão automática por inadimplência (>15 dias overdue)
- [ ] Grace period funcional
- [ ] Alertas de limite (80%, 100% SMS; trial expirando)
- [ ] Trial expirado → tenant suspenso
- [ ] Auditoria global imutável
- [ ] Dashboard financeiro com métricas
- [ ] Exportação CSV funcional
- [ ] Jobs agendados configurados e testados
- [ ] UsageMetricsMiddleware integrado em pelo menos 1 módulo (comunicação)
- [ ] Testes passando
