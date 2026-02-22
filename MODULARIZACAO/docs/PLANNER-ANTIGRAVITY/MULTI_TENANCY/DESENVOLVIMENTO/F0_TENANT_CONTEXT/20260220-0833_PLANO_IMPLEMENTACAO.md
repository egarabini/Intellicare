# F0 — Plano de Implementação: TenantContext + Infraestrutura

> **Fase:** 0 | **DEV Atribuído:** DEV 1 (Core)  
> **Depende de:** Nenhuma | **Bloqueia:** F1, F2, F3, F4, F5

---

## Ordem de Execução

| # | Task | Estimativa | Critério de Aceite |
|---|---|---|---|
| 1 | Criar pacote `intellicare_core/tenant/` | 0.5 dia | Importável, testes unitários passam |
| 2 | Implementar `TenantContext` | 0.5 dia | `from_jwt()` e `default()` funcionam; dataclass imutável |
| 3 | Implementar `TenantAwareSessionFactory` | 1 dia | `SET search_path` executa corretamente; queries isoladas |
| 4 | Implementar `TenantRedisClient` | 0.5 dia | Keys prefixadas; get/set/delete/publish isolados |
| 5 | Atualizar `BaseModuleConfig` | 0.5 dia | `multi_tenant_enabled` e `default_tenant_id` disponíveis |
| 6 | Atualizar `OperationalDataAccess` | 0.5 dia | Aceita `tenant_ctx`; backward-compatible (sem ctx = comportamento atual) |
| 7 | Implementar `TenantLogFilter` | 0.25 dia | Logs incluem `[tenant_id]` em todas linhas |
| 8 | Criar `tenant_middleware.py` em `intellicare-auth` | 0.5 dia | `get_tenant_context()` extrai do JWT; 403 se ausente |
| 9 | Configurar Keycloak mapper | 0.25 dia | JWT contém claim `tenant_id` |
| 10 | Script de provisionamento de schema | 0.5 dia | `provision_tenant.py` cria schema + roda migrations |
| 11 | Testes de integração | 1 dia | Todos os cenários CT-01..CT-07 passando |

**Total: 5 dias**

---

## Detalhamento por Task

### Task 1-2: Pacote `tenant/` + TenantContext

```
Criar:
  intellicare_core/tenant/__init__.py
  intellicare_core/tenant/context.py

Testar:
  - TenantContext.from_jwt(payload_valido) → ctx com tenant_id
  - TenantContext.from_jwt(payload_sem_tenant) → tenant_id="default"
  - TenantContext.default() → ctx single-tenant
  - Imutabilidade: ctx.tenant_id = "x" → FrozenInstanceError
```

### Task 3: TenantAwareSessionFactory

```
Criar:
  intellicare_core/tenant/session.py

Testar:
  - get_session(ctx_A) → SET search_path TO tenant_a
  - get_session(ctx_B) → SET search_path TO tenant_b
  - Query em session_A não retorna dados de session_B
```

> [!IMPORTANT]
> **Atenção:** O `SET search_path` deve ser executado ANTES de qualquer query na session. Verificar que o pool de conexões não reutiliza search_path de outra session.

### Task 4: TenantRedisClient

```
Criar:
  intellicare_core/tenant/redis.py

Testar:
  - set(ctx_A, "key", "val") → Redis key: "tenant:hosp_a:key"
  - get(ctx_B, "key") → None (isolamento)
  - delete(ctx_A, "key") → Remove apenas a key do tenant A
```

### Task 5-6: BaseModuleConfig + OperationalDataAccess

```
Modificar:
  intellicare_core/config/base.py  (adicionar 2 campos)
  intellicare_core/data_access/operational.py  (adicionar param tenant_ctx)

Testar:
  - Sem tenant_ctx → comportamento idêntico ao atual (backward-compatible)
  - Com tenant_ctx → schema é prefixado com tenant
```

> [!CAUTION]
> **Backward Compatibility é CRÍTICA.** Nenhum módulo existente pode quebrar após esta mudança. O `tenant_ctx` deve ser opcional com default `None`.

### Task 7: TenantLogFilter

```
Criar:
  intellicare_core/logging/tenant_filter.py

Testar:
  - Log sem tenant configurado → [default]
  - Log com tenant configurado → [hospital_einstein]
```

### Task 8: TenantMiddleware (intellicare-auth)

```
Criar:
  intellicare_auth/tenant_middleware.py
Modificar:
  intellicare_auth/__init__.py

Testar:
  - Request com JWT válido + tenant_id → TenantContext retornado
  - Request com JWT válido SEM tenant_id → HTTP 403
  - Request sem JWT → HTTP 401 (comportamento existente do auth)
```

### Task 9: Keycloak Mapper

```
Configurar via Admin Console OU script:
  - Criar mapper "tenant_id" no client IntelliCare
  - Tipo: User Attribute → tenant_id
  - Add to access token: ✅
  - Add to ID token: ✅

Testar:
  - Login de teste retorna JWT com tenant_id no payload
```

### Task 10: Script de Provisionamento

```
Criar:
  intellicare-core/scripts/provision_tenant.py

O script deve:
  1. Receber tenant_id como argumento
  2. Criar schema "tenant_{tenant_id}" no PostgreSQL
  3. Rodar todas as migrations do Alembic nesse schema
  4. Inserir seed data (roles padrão, configs iniciais)
  5. Retornar status de sucesso/falha

Testar:
  - provision_tenant.py --tenant-id=teste_123
  - Verificar que schema foi criado
  - Verificar que tabelas existem no schema
```

### Task 11: Testes de Integração

```
Criar:
  tests/test_multi_tenant/test_isolation.py
  tests/test_multi_tenant/test_context.py
  tests/test_multi_tenant/test_session.py

Cenários:
  - CT-01 a CT-07 da Especificação Funcional
  - Cross-tenant query deve retornar 0 resultados
  - Redis cross-tenant deve retornar None
```

---

## Checklist de Entrega (para aprovação do Planner)

- [ ] `TenantContext` implementado e testado
- [ ] `TenantAwareSessionFactory` implementado e testado
- [ ] `TenantRedisClient` implementado e testado
- [ ] `BaseModuleConfig` atualizado (backward-compatible)
- [ ] `OperationalDataAccess` atualizado (backward-compatible)
- [ ] `TenantLogFilter` implementado
- [ ] `get_tenant_context()` em `intellicare-auth`
- [ ] Keycloak mapper configurado
- [ ] Script de provisionamento funcional
- [ ] Testes de integração passando (CT-01..CT-07)
- [ ] Nenhum módulo existente quebrou (rodar suíte completa)
