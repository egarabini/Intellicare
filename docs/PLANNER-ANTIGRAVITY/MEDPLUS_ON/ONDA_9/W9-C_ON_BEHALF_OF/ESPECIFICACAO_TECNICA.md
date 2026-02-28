# W9-C — On-behalf-of — Especificação Técnica

**Workstream:** W9-C
**Módulo:** `intellicare-auth` + `intellicare-core`
**Data:** 2026-02-24

---

## 1. Arquitetura

```
Request
    │
    │ Authorization: Bearer {token}
    │ X-On-Behalf-Of: Practitioner/123
    ▼
┌─────────────────────────────────────────────────┐
│  Auth Middleware (intellicare-auth)              │
│  1. Valida token → user_actor                    │
│  2. Se X-On-Behalf-Of presente:                  │
│     - Resolve user_id do delegado                │
│     - Valida permissão (on_behalf_of_allowed)    │
│     - Injeta on_behalf_of_user no request.state  │
│  3. request.state.actor = user_actor             │
│     request.state.on_behalf_of = user_delegado   │
└─────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────┐
│  Authorization / Access Policy                   │
│  - Usa on_behalf_of (se presente) para checks   │
│  - Ex: can_read(Patient, on_behalf_of)           │
└─────────────────────────────────────────────────┘
```

---

## 2. Implementação

### Middleware

```python
# intellicare_auth/middleware.py

async def on_behalf_of_middleware(request, call_next):
    actor = request.state.user  # do token
    on_behalf_of_header = request.headers.get("X-On-Behalf-Of")
    
    if on_behalf_of_header:
        delegate = await resolve_and_validate_delegate(actor, on_behalf_of_header)
        if not delegate:
            return JSONResponse(status_code=403, content={"error": "delegation_denied"})
        request.state.on_behalf_of = delegate
        request.state.audit_actor = actor  # para auditoria
    else:
        request.state.on_behalf_of = None
    
    response = await call_next(request)
    return response
```

### Validação

```python
async def resolve_and_validate_delegate(actor, header_value) -> User | None:
    # Parse: "Practitioner/123" ou "user-uuid"
    delegate_id = parse_reference(header_value)
    delegate = await get_user(delegate_id)
    if not delegate:
        return None
    if delegate.tenant_id != actor.tenant_id:
        return None
    if not actor.has_permission("on_behalf_of"):
        return None
    # Opcional: verificar relação (ex: mesmo projeto, hierarquia)
    return delegate
```

### Auditoria

```python
# Em cada ação sensível
audit_log.record(
    action="read",
    resource="Patient/123",
    actor=request.state.user.id,
    on_behalf_of=request.state.on_behalf_of.id if request.state.on_behalf_of else None,
)
```

---

## 3. Configuração

### Keycloak / RBAC
- Nova permission: `on_behalf_of` ou role `delegator`
- Mapear para coordenadores, secretárias, supervisores

### Variáveis
| Variável | Default | Descrição |
|----------|---------|-----------|
| `ON_BEHALF_OF_ENABLED` | true | Habilitar feature |
| `ON_BEHALF_OF_AUDIT` | true | Registrar em auditoria |

---

## 4. Estrutura de Código

```
intellicare-auth/
├── intellicare_auth/
│   ├── middleware.py      # Adicionar on_behalf_of
│   ├── delegation.py      # NOVO — resolve_and_validate
│   └── audit.py          # Adicionar on_behalf_of em logs
```
