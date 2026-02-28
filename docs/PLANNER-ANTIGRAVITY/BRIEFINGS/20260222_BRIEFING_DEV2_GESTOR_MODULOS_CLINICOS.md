# 📋 BRIEFING DEV2 — Tarefas T2-F2 + T2-F4
**Data:** 2026-02-22  
**Prazo estimado:** 5-7 dias (paralelo)  
**Prioridade:** 🟡 Alta — core multi-tenancy  
**Conflito com outras trilhas:** ZERO — Dev1 está no Traefik (T1-F3)

---

## 🎯 Resumo

Duas tarefas paralelas:

| # | Tarefa | O que é | Esforço |
|---|---|---|---|
| **T2-F2** | `intellicare-gestor` | **NOVO módulo** — gestão de usuários, RBAC, setores por tenant | 4-5 dias |
| **T2-F4** | Módulos clínicos multi-tenant | **REFACTOR** — injetar TenantContext nos 8 módulos existentes | 3-5 dias |

> [!IMPORTANT]
> **T2-F2 é 100% novo código.** T2-F4 é refactor dos módulos existentes. Podem ser feitos em sequência (F2 primeiro) ou parcialmente em paralelo.

---

# 📦 TAREFA 1: T2-F2 — intellicare-gestor

## O que é

Módulo de gestão **POR TENANT**. Diferente do `intellicare-admin` (que é da **plataforma**), o `intellicare-gestor` é usado pelo **administrador local de cada organização** para gerenciar seus próprios usuários, permissões e setores.

**Referência completa:** Ler estes 2 arquivos antes de começar:
- `docs/PLANNER-ANTIGRAVITY/MULTI_TENANCY/DESENVOLVIMENTO/F2_INTELLICARE_GESTOR/20260220-0839_ESPECIFICACAO_FUNCIONAL.md`
- `docs/PLANNER-ANTIGRAVITY/MULTI_TENANCY/DESENVOLVIMENTO/F2_INTELLICARE_GESTOR/20260220-0839_ESPECIFICACAO_TECNICA.md`

## Diferença Admin vs Gestor

| | intellicare-admin (F1 ✅ DONE) | intellicare-gestor (F2 — esta tarefa) |
|---|---|---|
| **Quem usa** | Super-admin da plataforma | Admin local da organização |
| **Schema** | `platform` | `tenant_{id}` |
| **Gerencia** | Tenants, planos, billing | Usuários, roles, setores |
| **Porta** | 8010 | **8011** |
| **Acesso** | Super-admin global | Admin do próprio tenant só |

## Estrutura de Arquivos a Criar

```
intellicare-gestor/
├── gestor/
│   ├── __init__.py
│   ├── config.py                  # GestorConfig (herda BaseModuleConfig)
│   ├── permissions.py             # Registry de permissões válidas
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py                # TenantUser ORM
│   │   ├── role.py                # Role, UserRole ORM
│   │   ├── sector.py              # Sector ORM
│   │   ├── settings.py            # TenantSetting ORM
│   │   └── audit.py               # LocalAuditLog ORM
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── user_schemas.py
│   │   ├── role_schemas.py
│   │   ├── sector_schemas.py
│   │   └── settings_schemas.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── user_service.py        # CRUD + limite de users + convite + KC sync
│   │   ├── role_service.py        # RBAC logic + validation
│   │   ├── sector_service.py
│   │   ├── settings_service.py
│   │   └── audit_service.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── app.py                 # FastAPI (usar intellicare-admin como referência)
│   │   ├── deps.py                # DI: session via TenantAwareSessionFactory
│   │   ├── user_routes.py
│   │   ├── role_routes.py
│   │   ├── sector_routes.py
│   │   ├── settings_routes.py
│   │   ├── audit_routes.py
│   │   └── dashboard_routes.py
│   └── scripts/
│       └── seed_roles.py          # Seed das 6 roles padrão
├── tests/
│   ├── conftest.py
│   ├── test_user_service.py
│   ├── test_role_service.py
│   └── test_permissions.py
├── pyproject.toml
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## Modelos ORM (copiar da spec técnica, mas resumindo)

### TenantUser
```python
class TenantUser(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    keycloak_user_id = Column(String(255), unique=True)
    nome = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    cpf = Column(String(14), unique=True)
    cargo = Column(String(100))    # "Médico", "Enfermeiro"
    conselho = Column(String(50))  # "CRM-SP 123456"
    sector_id = Column(UUID, ForeignKey("sectors.id"))
    active = Column(Boolean, default=True)
    invited_at = Column(DateTime)
    last_login_at = Column(DateTime)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
```

### Role + UserRole
```python
class Role(Base):
    __tablename__ = "roles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, unique=True)
    display_name = Column(String(255))
    is_system = Column(Boolean, default=False)       # True = seed, não pode deletar
    permissions = Column(JSON, default=[])            # ["oswaldo.classificar", "florence.ver"]
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))

class UserRole(Base):
    __tablename__ = "user_roles"
    user_id = Column(UUID, ForeignKey("users.id"), primary_key=True)
    role_id = Column(UUID, ForeignKey("roles.id"), primary_key=True)
    assigned_at = Column(DateTime, default=lambda: datetime.now(UTC))
    assigned_by = Column(UUID)
```

### Sector, TenantSetting, LocalAuditLog
Definidos na spec técnica — seguir exatamente o que está lá.

## 14 Endpoints

| Método | Endpoint | Descrição |
|---|---|---|
| `GET` | `/gestor/users` | Listar usuários do tenant |
| `POST` | `/gestor/users` | Criar/convidar usuário |
| `PATCH` | `/gestor/users/{id}` | Atualizar usuário |
| `DELETE` | `/gestor/users/{id}` | Desativar (soft delete) |
| `GET` | `/gestor/roles` | Listar roles |
| `POST` | `/gestor/roles` | Criar role customizada |
| `PATCH` | `/gestor/roles/{id}` | Atualizar permissões |
| `GET` | `/gestor/sectors` | Listar setores |
| `POST` | `/gestor/sectors` | Criar setor |
| `PATCH` | `/gestor/sectors/{id}` | Atualizar setor |
| `GET` | `/gestor/settings` | Listar configs |
| `PATCH` | `/gestor/settings` | Atualizar configs |
| `GET` | `/gestor/audit` | Logs de auditoria |
| `GET` | `/gestor/dashboard` | Dashboard do gestor |

## Regras de Negócio Críticas

### 1. Limite de Usuários
```python
# user_service.py — ao criar usuário:
async def create_user(self, data, ctx: TenantContext):
    # Contar users ativos
    count = await self._count_active_users()
    
    # Buscar limite do plano (na tabela platform.tenants)
    tenant = await self._get_tenant_info(ctx.tenant_id)  # Query no schema platform
    
    if count >= tenant.max_users:
        raise HTTPException(402, "Limite de usuários atingido para seu plano")
```

### 2. Proteção de Admin
```python
# Ao desativar usuário:
async def deactivate_user(self, user_id, ctx):
    # Verificar se é o último admin_local
    admin_count = await self._count_users_with_role("admin_local")
    if admin_count <= 1 and user_has_role(user_id, "admin_local"):
        raise HTTPException(400, "Deve haver pelo menos 1 administrador")
```

### 3. Validação de Permissões
```python
# permissions.py — já definido na spec:
VALID_PERMISSIONS = {
    "zilda": ["ver", "buscar", "editar"],
    "oswaldo": ["classificar", "ver", "exportar"],
    "florence": ["analisar", "ver_resultados", "exportar"],
    "geralda": ["ver", "plano_cuidado", "alertas"],
    "donabedian": ["ver", "avaliar", "relatorios"],
    "comunicacao": ["enviar_sms", "enviar_email", "ver", "configurar"],
    "grahame": ["fhir_read", "fhir_write", "fhir_search"],
    "wanda": ["consultar", "configurar"],
    "gestor": ["usuarios", "roles", "setores", "configs", "auditoria"],
}
```

### 4. TenantContext — O MAIS IMPORTANTE
```python
# deps.py — diferente do admin:
async def get_session(request: Request, ctx: TenantContext = Depends(get_tenant_context)):
    """Session no schema do tenant (não platform!)."""
    factory: TenantAwareSessionFactory = request.app.state.session_factory
    session = await factory.get_session(ctx)  # SET search_path = tenant_{id}
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
```

> [!CAUTION]
> O `intellicare-admin` opera no schema `platform`. O `intellicare-gestor` opera no schema `tenant_{id}`. Esta é a diferença fundamental. Usar `TenantAwareSessionFactory.get_session(ctx)` para garantir isolamento.

## Seed Roles (inseridas pelo ProvisioningService quando tenant é criado)

```python
DEFAULT_ROLES = [
    {"name": "admin_local", "display_name": "Administrador Local", "is_system": True,
     "permissions": ["*"]},
    {"name": "gestor_setor", "display_name": "Gestor de Setor", "is_system": True,
     "permissions": ["gestor.usuarios", "gestor.setores"]},
    {"name": "medico", "display_name": "Médico", "is_system": True,
     "permissions": ["oswaldo.*", "florence.ver_resultados", "geralda.*", "comunicacao.enviar_email"]},
    {"name": "enfermeiro", "display_name": "Enfermeiro(a)", "is_system": True,
     "permissions": ["florence.*", "geralda.ver", "comunicacao.enviar_email"]},
    {"name": "tecnico", "display_name": "Técnico", "is_system": True,
     "permissions": ["florence.ver_resultados", "zilda.ver"]},
    {"name": "recepcao", "display_name": "Recepção", "is_system": True,
     "permissions": ["zilda.buscar", "comunicacao.ver"]},
]
```

## Referências para copiar padrões

| Pattern | Copiar de | Arquivo |
|---|---|---|
| `pyproject.toml` | `intellicare-admin/pyproject.toml` | Trocar nome e porta |
| `config.py` | `intellicare-admin/admin/config.py` | Simplificar (menos configs) |
| `app.py` | `intellicare-admin/admin/api/app.py` | Mesmo padrão, porta 8011 |
| `deps.py` | `intellicare-admin/admin/api/deps.py` | **MAS usar TenantAwareSessionFactory** |
| `Dockerfile` | `intellicare-admin/Dockerfile` | Trocar porta para 8011 |
| `docker-compose.yml` | `intellicare-admin/docker-compose.yml` | Trocar porta e nome |

---

# 🔧 TAREFA 2: T2-F4 — Módulos Clínicos Multi-Tenant

## O que é

Adaptar os **8 módulos clínicos existentes** para usar `TenantContext`. É um refactor: adicionar dependências nos endpoints, trocar sessions, prefixar Redis keys.

**Referência completa:**
- `docs/PLANNER-ANTIGRAVITY/MULTI_TENANCY/DESENVOLVIMENTO/F4_MODULOS_CLINICOS/20260220-0841_ESPECIFICACAO_FUNCIONAL.md`
- `docs/PLANNER-ANTIGRAVITY/MULTI_TENANCY/DESENVOLVIMENTO/F4_MODULOS_CLINICOS/20260220-0842_ESPECIFICACAO_TECNICA.md`

## Padrão de Refactoring (Aplicar a TODOS)

### ANTES (single-tenant):
```python
@router.get("/api/v1/data")
async def get_data(db: AsyncSession = Depends(get_db_session)):
    result = await db.execute(select(MyModel))
    return result.scalars().all()
```

### DEPOIS (multi-tenant):
```python
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

## Checklist de Módulos (em ordem de complexidade)

### 1. `intellicare-comunicacao` — 🔴 MAIS COMPLEXO (3 dias)

| Arquivo | O que mudar |
|---|---|
| `comunicacao/api/app.py` | Adicionar `check_module_active("comunicacao", ctx)` |
| `comunicacao/routing/engine.py` | `RoutingEngine.__init__` recebe `TenantContext` |
| `comunicacao/dispatchers/base.py` | `ChannelDispatcher.send()` recebe `ctx` |
| `comunicacao/channels/sms/dispatcher.py` | Config do SMS provider vem de `tenant_settings` |
| `comunicacao/channels/email/dispatcher.py` | SMTPConfig vem de `tenant_settings` |
| `comunicacao/lgpd/compliance_service.py` | Consentimentos isolados por tenant |
| `comunicacao/storage/repository.py` | Usar `TenantAwareSessionFactory` |

**Padrão para config por tenant nos dispatchers:**
```python
class SMSDispatcher(ChannelDispatcher):
    async def _get_config(self, ctx: TenantContext, session):
        # 1. Tentar config do tenant (tenant_{id}.settings)
        tenant_config = await session.execute(
            select(TenantSetting).where(
                TenantSetting.category == "comunicacao",
                TenantSetting.key == "sms_provider"
            )
        )
        config = tenant_config.scalar_one_or_none()
        if config:
            return config.value
        
        # 2. Fallback: config global (env var)
        return SMSConfig.from_env()
```

---

### 2. `intellicare-zilda` — 🟡 MÉDIO (1 dia)

| Arquivo | O que mudar |
|---|---|
| `zilda/api/routes.py` (ou equivalente) | Adicionar `ctx: TenantContext = Depends(get_tenant_context)` |
| Serviços de busca CNES | Redis key prefixada: `tenant:{id}:cnes:{code}` |

---

### 3. `intellicare-oswaldo` — 🟡 MÉDIO (1 dia)

| Arquivo | O que mudar |
|---|---|
| `oswaldo/api/routes.py` | Adicionar `TenantContext` |
| `oswaldo/services/classification.py` | Classificações salvas no schema do tenant |

---

### 4. `intellicare-florence` — 🟡 MÉDIO (1 dia)

| Arquivo | O que mudar |
|---|---|
| `florence/api/routes.py` | Adicionar `TenantContext` |
| `florence/services/analysis.py` | Resultados salvos no schema do tenant |

---

### 5-8. Geralda, Donabedian, Grahame, Wanda — 🟢 SIMPLES (0.5 dia cada)

Mesmo padrão: adicionar `TenantContext`, usar `TenantAwareSessionFactory`, prefixar Redis keys.

## Middleware de Módulo Ativo (Aplicar em TODOS os módulos)

```python
# Adicionar no app.py de cada módulo:
from intellicare_core.tenant import TenantContext, TenantRedisClient

MODULE_NAME = "oswaldo"  # trocar pelo nome do módulo

async def check_module_active(ctx: TenantContext):
    """Verifica se módulo está ativo para o tenant. Cached no Redis."""
    redis = TenantRedisClient(redis_url)
    cache_key = f"modules:{MODULE_NAME}:active"
    cached = await redis.get(ctx, cache_key)
    
    if cached is not None:
        if cached == "0":
            raise HTTPException(403, f"Módulo '{MODULE_NAME}' não disponível para sua organização")
        return
    
    # Fallback: consultar platform.tenant_modules
    # Query e cache com TTL de 5min
```

## REGRA CRÍTICA: Backward Compatibility

> [!CAUTION]
> **TODOS os módulos DEVEM continuar funcionando em modo single-tenant** (sem Keycloak/JWT) usando `TenantContext.default()`. Sem isso, o dev local quebra!

```python
# No app.py de cada módulo:
class ModuleConfig(BaseModuleConfig):
    multi_tenant_enabled: bool = False  # Default: single-tenant

config = ModuleConfig()

if config.multi_tenant_enabled:
    app.include_router(router, dependencies=[Depends(get_tenant_context)])
else:
    app.include_router(router)  # Sem tenant — funciona como antes
```

---

## ⚠️ Regras Gerais

> [!WARNING]
> 1. **NÃO alterar Dockerfiles** — Dev2 anterior já padronizou (T4-F2)
> 2. **NÃO alterar `docker-compose.full.yml`** — já correto
> 3. **NÃO tocar no `intellicare-admin`** — Dev1 mantém
> 4. **Manter backward compatibility** — single-tenant deve funcionar

> [!IMPORTANT]
> **Imports do TenantContext:**
> ```python
> from intellicare_core.tenant import TenantContext, TenantAwareSessionFactory, TenantRedisClient
> from intellicare_auth import get_tenant_context  # Middleware que extrai do JWT
> ```
> Esses já estão implementados e exportados. Só usar.

---

## 📁 Resumo de Arquivos

### T2-F2 (intellicare-gestor — NOVO)
| # | Arquivo | Tipo |
|---|---|---|
| 1-30 | `gestor/` inteiro | **NOVO** — ~30 arquivos |

### T2-F4 (módulos clínicos — REFACTOR)
| # | Módulo | Arquivos afetados (estimado) |
|---|---|---|
| 1 | comunicacao | ~7 arquivos |
| 2 | zilda | ~3 arquivos |
| 3 | oswaldo | ~3 arquivos |
| 4 | florence | ~3 arquivos |
| 5 | geralda | ~2 arquivos |
| 6 | donabedian | ~2 arquivos |
| 7 | grahame | ~2 arquivos |
| 8 | wanda | ~2 arquivos |

**Total estimado: ~54 arquivos (30 novos + 24 modificados)**

---

## 🏁 Critério de Conclusão

### T2-F2 (intellicare-gestor):
1. ✅ Todos os 14 endpoints funcionando
2. ✅ RBAC com permissões granulares
3. ✅ Limite de usuários respeita plano
4. ✅ Seed de 6 roles padrão
5. ✅ Audit log de todas as ações
6. ✅ Testes unitários

### T2-F4 (módulos clínicos):
1. ✅ Todos os 8 módulos aceitam `TenantContext`
2. ✅ Dados isolados por schema
3. ✅ Redis keys prefixadas por tenant
4. ✅ Middleware `check_module_active` em cada módulo
5. ✅ **Backward compatibility**: todos rodam sem JWT com `multi_tenant_enabled=false`
6. ✅ Nenhum módulo quebrou
