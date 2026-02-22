# F3 — Plano de Implementação: Portal Multi-Tenant

> **DEV Atribuído:** DEV 3 (Frontend)  
> **Depende de:** F0 ✅, F1 ✅ (endpoints de branding/módulos devem existir)  
> **Pode rodar em paralelo com:** F2, F4

---

## Ordem de Execução

| # | Task | Estimativa | Depende de |
|---|---|---|---|
| 1 | Instalar `jwt-decode` + criar `utils/jwt.ts` | 0.25 dia | — |
| 2 | Criar `TenantContext.tsx` + `useTenantContext.ts` | 1 dia | Task 1 |
| 3 | Wrap `App.tsx` com `TenantProvider` | 0.25 dia | Task 2 |
| 4 | CSS Variables dinâmicas + `applyBranding()` | 0.5 dia | Task 2 |
| 5 | `ModuleRoute` — route guard por módulo ativo | 0.5 dia | Task 2 |
| 6 | Filtrar módulos no Dashboard | 0.5 dia | Tasks 2, 5 |
| 7 | Header com branding do tenant | 0.5 dia | Task 4 |
| 8 | Testes manuais com 2 tenants | 1 dia | Todas |
| 9 | Documentação (README update) | 0.5 dia | Task 8 |

**Total: 5 dias**

---

## Checklist de Entrega

- [ ] JWT decodificado e `tenant_id` extraído
- [ ] `TenantProvider` wrapping toda a aplicação
- [ ] Branding dinâmico (cores, logo, nome)
- [ ] Módulos filtrados no dashboard
- [ ] Rotas protegidas por módulo ativo
- [ ] Header exibe info do tenant
- [ ] Fallback para tema IntelliCare padrão
- [ ] Testado com 2 tenants diferentes
- [ ] Nenhuma URL expõe tenant_id
