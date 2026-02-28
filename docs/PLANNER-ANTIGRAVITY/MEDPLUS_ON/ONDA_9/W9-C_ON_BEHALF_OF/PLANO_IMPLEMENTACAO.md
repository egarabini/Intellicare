# W9-C — On-behalf-of — Plano de Implementação

**Workstream:** W9-C
**Estimativa:** 5 dias
**Responsável:** DEV0

---

## Ordem de Execução

| # | Task | Dias | Depende |
|---|------|------|---------|
| 1 | Criar `delegation.py` (resolve, validate) | 1 | — |
| 2 | Adicionar middleware on_behalf_of | 1 | 1 |
| 3 | Integrar com Access Policy (usar on_behalf_of) | 1 | 2 |
| 4 | Auditoria (actor + on_behalf_of) | 1 | 2 |
| 5 | Configurar role/permission no Keycloak | 0.5 | — |
| 6 | Testes | 0.5 | 1-4 |

---

## Passo a Passo

### Passo 1: delegation.py
- `parse_reference(header)` → user_id
- `resolve_and_validate_delegate(actor, header)` → User | None
- Regras: mesmo tenant, permission on_behalf_of

### Passo 2: Middleware
- Ler X-On-Behalf-Of
- Chamar resolve_and_validate
- Injetar request.state.on_behalf_of
- 403 se inválido

### Passo 3: Access Policy
- Onde hoje usa `request.state.user` para authz, usar `request.state.on_behalf_of or request.state.user`
- Garantir que recursos são filtrados pelo delegado

### Passo 4: Auditoria
- Em audit_log.record, adicionar on_behalf_of
- Garantir que actor (quem fez) e on_behalf_of (em nome de quem) estão registrados

### Passo 5: Keycloak
- Criar permission `on_behalf_of` ou role `delegator`
- Atribuir a coordenadores, secretárias

### Passo 6: Testes
- test_delegation_valid
- test_delegation_invalid_tenant
- test_delegation_no_permission
- test_audit_includes_on_behalf_of

---

## Checklist de Entrega

- [ ] X-On-Behalf-Of processado
- [ ] Validação de permissão
- [ ] Auditoria com actor + on_behalf_of
- [ ] Testes passando
