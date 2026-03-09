# 📅 W2-A — Plano de Implementação: Bots Engine

## Visão Geral
- **Duração:** 14 dias úteis (2 sprints)
- **Devs:** 2 (Dev 1 + Dev 2)
- **Pré-requisito:** Onda 1 completa (Subscriptions Engine funcional)

---

## Sprint 1 (Dias 1-7) — Core Engine

### Dia 1-2: Modelos + CRUD (Dev 1 + Dev 2)
- [ ] Criar package `intellicare_core/bots/`
- [ ] Implementar `models.py` (bots, bot_secrets, bot_executions)
- [ ] Criar migrations Alembic
- [ ] CRUD API no Grahame para Bot resource

### Dia 3-4: Sandbox Python (Dev 1)
- [ ] Implementar `sandbox.py` com RestrictedPython
- [ ] Allowlist de imports
- [ ] Timeout enforcement
- [ ] Testes de segurança (tentar escapar sandbox)

### Dia 3-4: Client + Context (Dev 2)
- [ ] Implementar `client.py` — IntelliCareClient FHIR
- [ ] Implementar `context.py` — BotExecutionContext
- [ ] Implementar `secrets_manager.py` — Fernet encryption

### Dia 5-6: Integração (Dev 1 + Dev 2)
- [ ] Atualizar `bot_channel.py` (stub → implementação real)
- [ ] Implementar `executor.py` — orquestrador
- [ ] Teste e2e: Subscription → Bot → FHIR action

### Dia 7: Review + Testes
- [ ] Code review cruzado
- [ ] Testes de multi-tenancy
- [ ] PR #1

---

## Sprint 2 (Dias 8-14) — Observabilidade + UI + Exemplos

### Dia 8-9: Audit + Métricas (Dev 1)
- [ ] Implementar `audit.py`
- [ ] Métricas Prometheus (bot_executions_total, bot_duration_seconds)
- [ ] Logging estruturado

### Dia 10-11: UI no Gestor (Dev 2)
- [ ] Página de listagem de bots
- [ ] Editor de código simples
- [ ] Visualização de logs de execução
- [ ] Toggle enable/disable

### Dia 12-13: Bots Exemplo (Dev 1 + Dev 2)
- [ ] Bot: Alerta de glicose alta
- [ ] Bot: Welcome patient
- [ ] Bot: Lab result notification
- [ ] Bot: Protocol adherence check
- [ ] Bot: Quality indicator update

### Dia 14: Finalização
- [ ] Documentação completa
- [ ] PR #2, merge final

---

## Critérios de Aceite

1. ✅ Bot executa em sandbox sem acesso ao filesystem
2. ✅ Client FHIR funcional dentro do bot
3. ✅ Secrets encriptados at-rest
4. ✅ Timeout enforced (30s padrão)
5. ✅ AuditEvent e logs persistidos
6. ✅ Multi-tenancy comprovado
7. ✅ 5 bots exemplo funcionais
