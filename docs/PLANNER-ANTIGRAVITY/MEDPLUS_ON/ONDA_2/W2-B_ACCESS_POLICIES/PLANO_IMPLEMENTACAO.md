# 📅 W2-B — Plano de Implementação: FHIR Access Policies

## Visão Geral
- **Duração:** 14 dias úteis (2 sprints)
- **Devs:** 2 (Dev 3 + Dev 4)
- **Pré-requisito:** Onda 1 completa

---

## Sprint 1 (Dias 1-7) — Core Policy Engine

### Dia 1-2: Modelos + CRUD (Dev 3 + Dev 4)
- [ ] Criar package `intellicare_core/access/`
- [ ] Implementar `models.py` (access_policies, tenant_membership_policies)
- [ ] Criar migrations Alembic
- [ ] CRUD API de AccessPolicy no Gestor

### Dia 3-4: Policy Builder (Dev 3)
- [ ] Implementar `policy_builder.py`
- [ ] Carregar policies por membership
- [ ] Composição de múltiplas policies
- [ ] Parametrização (`%profile`, `%patient`)
- [ ] Cache de policies (Redis, TTL 5min)

### Dia 3-4: Policy Evaluator (Dev 4)
- [ ] Implementar `policy_evaluator.py`
- [ ] Check de interaction (search, read, create, update, delete)
- [ ] Criteria matching (reuso do FHIRCriteriaMatcher da W1-B)
- [ ] Testes unitários (25+ cenários)

### Dia 5-6: Field Filter + Compartment (Dev 3 + Dev 4)
- [ ] Implementar `field_filter.py` (hidden + readonly)
- [ ] Implementar `compartment.py` (Organization scoping)
- [ ] Testes de campo-level

### Dia 7: Review + Integration Tests
- [ ] Code review cruzado
- [ ] Testes de composição de policies
- [ ] PR #1

---

## Sprint 2 (Dias 8-14) — Middleware + Integração

### Dia 8-9: Middleware (Dev 3)
- [ ] Implementar `access_middleware.py`
- [ ] Resolver policy do JWT (Keycloak user_id → memberships)
- [ ] Adicionar ao pipeline de request dos módulos

### Dia 8-9: SMART Scopes (Dev 4)
- [ ] Implementar `smart_scopes.py`
- [ ] Parser de scopes (`patient/*.read`, `user/Observation.write`)
- [ ] Aplicação de scopes sobre policy existente

### Dia 10-11: Integração no Grahame (Dev 3 + Dev 4)
- [ ] Aplicar middleware em todos os endpoints FHIR
- [ ] Filtrar campos na resposta (hidden)
- [ ] Bloquear writes em campos readonly
- [ ] Testes e2e com 5 personas

### Dia 12-13: Policies Exemplo + Gestor UI (Dev 3 + Dev 4)
- [ ] Criar 5 policies default (médico, enfermeiro, recepcionista, admin, sistema)
- [ ] UI no Gestor para gestão de policies
- [ ] Atribuição de policies a memberships

### Dia 14: Finalização
- [ ] Documentação completa
- [ ] PR #2, merge final

---

## Critérios de Aceite

1. ✅ Middleware funcional em todos os endpoints FHIR
2. ✅ 5 policies default funcionais
3. ✅ Campo hidden realmente não aparece na resposta
4. ✅ Campo readonly bloqueia update
5. ✅ Compartment limita acesso por Organization
6. ✅ SMART scopes básicos funcionais
7. ✅ Integração com Keycloak JWT
8. ✅ Cobertura ≥ 85%
