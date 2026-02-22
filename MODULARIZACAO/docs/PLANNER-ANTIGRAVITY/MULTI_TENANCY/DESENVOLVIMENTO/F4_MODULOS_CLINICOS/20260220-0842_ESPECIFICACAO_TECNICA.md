# F4 — Especificação Técnica: Adaptação dos Módulos Clínicos

> **Módulos:** Todos os agentes + comunicação  
> **Depende de:** F0 (usar contratos publicados)

---

## 1. Padrão de Refactoring (Template para Todos os Módulos)

### 1.1 — Antes (Single-Tenant)

```python
# Endpoint atual (sem tenant)
@router.get("/api/v1/data")
async def get_data(db: AsyncSession = Depends(get_db_session)):
    result = await db.execute(select(MyModel))
    return result.scalars().all()
```

### 1.2 — Depois (Multi-Tenant)

```python
# Endpoint multi-tenant
from intellicare_auth import get_tenant_context
from intellicare_core.tenant import TenantContext, TenantAwareSessionFactory

@router.get("/api/v1/data")
async def get_data(
    ctx: TenantContext = Depends(get_tenant_context),
    session_factory: TenantAwareSessionFactory = Depends(get_session_factory),
):
    session = await session_factory.get_session(ctx)  # search_path = tenant_{id}
    result = await session.execute(select(MyModel))
    return result.scalars().all()
```

### 1.3 — Middleware de Módulo Ativo

```python
# Aplicar em cada módulo no app.py
from intellicare_core.tenant import TenantContext

async def check_module_active(module_name: str, ctx: TenantContext):
    """Verifica se módulo está ativo para o tenant."""
    # Verificar via cache Redis (TTL 5min)
    redis = TenantRedisClient(redis_url)
    cache_key = f"modules:{module_name}:active"
    cached = await redis.get(ctx, cache_key)
    
    if cached is not None:
        if cached == "0":
            raise HTTPException(403, f"Módulo '{module_name}' não disponível")
        return
    
    # Fallback: consultar platform.tenant_modules
    # ... query e cache do resultado
```

---

## 2. Alterações por Módulo

### 2.1 — `intellicare-comunicacao` (5 dias)

**Arquivos afetados:**

| Arquivo | Alteração |
|---|---|
| `api/app.py` | Injetar `check_module_active("comunicacao", ctx)` no lifespan |
| `routing/engine.py` | `RoutingEngine.__init__` recebe `TenantContext` |
| `dispatchers/base.py` | `ChannelDispatcher.send()` recebe `ctx` |
| `channels/sms/dispatcher.py` | Config do provider vem de `tenant_settings` |
| `channels/email/dispatcher.py` | SMTPConfig vem de `tenant_settings` |
| `lgpd/compliance_service.py` | Consentimentos isolados por tenant |
| `storage/repository.py` | Usar `TenantAwareSessionFactory` |

**Padrão para config por tenant nos dispatchers:**

```python
class SMSDispatcher(ChannelDispatcher):
    def __init__(self, ctx: TenantContext, session_factory):
        self._ctx = ctx
        session = await session_factory.get_session(ctx)
        
        # Buscar config do tenant
        tenant_config = await self._load_tenant_sms_config(session)
        if tenant_config:
            self._provider = self._create_provider(tenant_config)
        else:
            # Fallback para config global
            self._provider = self._create_provider(SMSConfig.from_env())
```

### 2.2 — `intellicare-zilda` (2 dias)

**Arquivos afetados:**

| Arquivo | Alteração |
|---|---|
| `zilda/config.py` | Manter como está (config global) |
| `api/routes.py` | Adicionar `ctx: TenantContext = Depends(get_tenant_context)` |
| Serviços de busca CNES | Redis key prefixada: `tenant:{id}:cnes:{code}` |

### 2.3 — `intellicare-oswaldo` (2 dias)

| Arquivo | Alteração |
|---|---|
| `api/routes.py` | Adicionar `TenantContext` |
| `services/classification.py` | Classificações salvas no schema do tenant |
| `profiles/` | Perfis de doenças: compartilhados (global) ou por tenant |

### 2.4 — `intellicare-florence` (2 dias)

| Arquivo | Alteração |
|---|---|
| `api/routes.py` | Adicionar `TenantContext` |
| `services/analysis.py` | Resultados salvos no schema do tenant |

### 2.5 — Demais Módulos (Geralda, Donabedian, Grahame, Wanda — 2 dias cada)

Mesmo padrão: adicionar `TenantContext`, usar `TenantAwareSessionFactory`, prefixar Redis keys.

---

## 3. Ordem de Implementação Sugerida

1. **Comunicação** (mais complexo — resolver primeiro)
2. **Zilda** (usado por quase todos os tenants)
3. **Oswaldo** e **Florence** (em paralelo se 2 DEVs)
4. **Geralda**, **Donabedian**, **Grahame**, **Wanda** (simples, um por dia)

---

## 4. Backward Compatibility

> [!CAUTION]
> **TODOS os módulos DEVEM continuar funcionando em modo single-tenant** (sem Keycloak/JWT) usando `TenantContext.default()`. Isso é essencial para desenvolvimento local e testes.

```python
# Em cada módulo, o config deve ter:
class ModuleConfig(BaseModuleConfig):
    multi_tenant_enabled: bool = False  # Herdado de BaseModuleConfig

# No app.py:
if config.multi_tenant_enabled:
    app.include_router(router, dependencies=[Depends(get_tenant_context)])
else:
    app.include_router(router)  # Sem tenant middleware
```
