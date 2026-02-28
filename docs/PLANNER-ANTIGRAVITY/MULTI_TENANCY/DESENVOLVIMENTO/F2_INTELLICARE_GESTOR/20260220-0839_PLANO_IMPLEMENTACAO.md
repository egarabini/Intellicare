# F2 — Plano de Implementação: intellicare-gestor

> **DEV Atribuído:** DEV 2 ou DEV 3  
> **Depende de:** F0 ✅, F1 (ProvisioningService cria o schema e seed data)  
> **Pode rodar em paralelo com:** F3, F5

---

## Ordem de Execução

| # | Task | Estimativa | Depende de |
|---|---|---|---|
| 1 | Scaffold do módulo | 0.5 dia | F1 completo |
| 2 | Modelos ORM (users, roles, sectors, settings, audit) | 1 dia | Task 1 |
| 3 | Pydantic Schemas | 0.5 dia | Task 2 |
| 4 | Permission Registry (`permissions.py`) | 0.5 dia | — |
| 5 | UserService + KC sync | 1.5 dias | Tasks 2, 3 |
| 6 | RoleService + permission middleware | 1 dia | Tasks 2, 4 |
| 7 | SectorService + SettingsService | 0.5 dia | Task 2 |
| 8 | API Routes (users, roles, sectors, settings, audit) | 1 dia | Tasks 5-7 |
| 9 | Dashboard route + métricas | 0.5 dia | Task 8 |
| 10 | Testes | 1.5 dias | Todas |
| 11 | Integrar seed data no ProvisioningService (F1) | 0.5 dia | F1.Task5, Task 2 |

**Total: 8 dias**

---

## Checklist de Entrega

- [ ] CRUD de usuários (criar, listar, atualizar, desativar)
- [ ] Limite de usuários respeita plano do tenant
- [ ] Convite por email funcional (via intellicare-comunicacao)
- [ ] RBAC: roles + permissões funcionando
- [ ] Roles seed inseridos pelo provisioning
- [ ] Setores CRUD com hierarquia simples
- [ ] Settings CRUD por tenant
- [ ] Auditoria local registrando ações
- [ ] Dashboard com métricas básicas
- [ ] Cross-tenant isolation (tenant A ≠ tenant B)
- [ ] Testes passando
