# F4 — Plano de Implementação: Módulos Clínicos

> **DEV Atribuído:** DEV 1 ou DEV 4 (pode dividir entre 2 DEVs)  
> **Depende de:** F0 ✅ APENAS  
> **Pode rodar em paralelo com:** F1, F2, F3, F5

---

## Ordem de Execução

| # | Task | Estimativa | DEV |
|---|---|---|---|
| 1 | `intellicare-comunicacao` — Routing + Dispatchers | 3 dias | DEV A |
| 2 | `intellicare-comunicacao` — LGPD + Templates | 2 dias | DEV A |
| 3 | `intellicare-zilda` — Cache + Routes | 1 dia | DEV B |
| 4 | `intellicare-oswaldo` — Classification + Profiles | 1 dia | DEV B |
| 5 | `intellicare-florence` — Analysis service | 1 dia | DEV A ou B |
| 6 | `intellicare-geralda` — Care plans | 0.5 dia | DEV A ou B |
| 7 | `intellicare-donabedian` — Quality indicators | 0.5 dia | DEV A ou B |
| 8 | `intellicare-grahame` — FHIR resources | 0.5 dia | DEV A ou B |
| 9 | `intellicare-wanda` — IA context | 0.5 dia | DEV A ou B |
| 10 | Testes de isolamento cross-tenant | 1.5 dias | Ambos |

**Total: 10 dias (5 dias se 2 DEVs em paralelo)**

> [!TIP]
> **Melhor estratégia com 2 DEVs:** DEV A faz comunicação (tasks 1-2), DEV B faz todos os outros (tasks 3-9). Ambos fazem testes (task 10).

---

## Checklist de Entrega (por módulo)

Para **CADA** módulo, verificar:

- [ ] `TenantContext` injetado em todos os endpoints
- [ ] `TenantAwareSessionFactory` usado para sessions
- [ ] Redis keys prefixadas com `tenant:{id}:`
- [ ] Config por tenant funcionando (settings override)
- [ ] Verificação de módulo ativo (HTTP 403 se desativado)
- [ ] Backward-compatible em modo single-tenant
- [ ] Testes de isolamento: tenant A ≠ tenant B
- [ ] Suíte de testes existente continua passando
