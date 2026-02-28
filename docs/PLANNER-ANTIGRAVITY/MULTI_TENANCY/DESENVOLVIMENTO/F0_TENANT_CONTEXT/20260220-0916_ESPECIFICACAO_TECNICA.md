# F0 — Especificação Técnica: TenantContext + Infraestrutura

> **Fase:** 0 | **Módulos:** `intellicare-core`, `intellicare-auth`  
> **Stack:** Python 3.11+, FastAPI, SQLAlchemy 2.x, Redis, Keycloak 24+

---

## 1. Alterações em `intellicare-core`

### 1.1 — TenantContext (NOVO)

**Arquivo:** `intellicare_core/tenant/context.py`

```python
from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True, slots=True)
class TenantContext:
    """Contexto imutável do tenant para a requisição atual."""
    
    tenant_id: str
    tenant_schema: str
    user_id: str
    user_roles: list[str] = field(default_factory=list)
    available_tenants: list[str] = field(default_factory=list)  # Multi-org
    
    @classmethod
    def from_jwt(cls, payload: dict) -> "TenantContext":
        tenant_id = payload.get("tenant_id", "default")
        tenants = payload.get("tenants", [])
        return cls(
            tenant_id=tenant_id,
            tenant_schema=f"tenant_{tenant_id}",
            user_id=payload.get("sub", ""),
            user_roles=cls._extract_roles(payload),
            available_tenants=tenants,
        )
    
    @property
    def is_multi_org(self) -> bool:
        """Retorna True se o usuário tem acesso a múltiplos tenants."""
        return len(self.available_tenants) > 1
    
    @classmethod
    def default(cls) -> "TenantContext":
        """Modo single-tenant para compatibilidade."""
        return cls(
            tenant_id="default",
            tenant_schema="public",
            user_id="system",
            available_tenants=["default"],
        )
    
    @staticmethod
    def _extract_roles(payload: dict) -> list[str]:
        roles = []
        realm_access = payload.get("realm_access", {})
        roles.extend(realm_access.get("roles", []))
        resource_access = payload.get("resource_access", {})
        for client_roles in resource_access.values():
            roles.extend(client_roles.get("roles", []))
        return list(set(roles))
```

### 1.2 — TenantAwareSession (NOVO)

**Arquivo:** `intellicare_core/tenant/session.py`

```python
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import text

from intellicare_core.tenant.context import TenantContext


class TenantAwareSessionFactory:
    """Factory que cria sessions com search_path do tenant."""
    
    def __init__(self, database_url: str):
        self._engine = create_async_engine(database_url, pool_pre_ping=True)
        self._sessionmaker = async_sessionmaker(
            self._engine, 
            class_=AsyncSession, 
            expire_on_commit=False,
        )
    
    async def get_session(self, ctx: TenantContext) -> AsyncSession:
        """Retorna session com search_path configurado para o tenant."""
        session = self._sessionmaker()
        # SET search_path garante que todas as queries usem o schema do tenant
        await session.execute(
            text(f"SET search_path TO {ctx.tenant_schema}, public")
        )
        return session
```

### 1.3 — TenantRedisClient (NOVO)

**Arquivo:** `intellicare_core/tenant/redis.py`

```python
import redis.asyncio as aioredis
from intellicare_core.tenant.context import TenantContext


class TenantRedisClient:
    """Redis client com prefixo de tenant automático."""
    
    def __init__(self, redis_url: str):
        self._redis = aioredis.from_url(redis_url)
    
    def _key(self, ctx: TenantContext, key: str) -> str:
        return f"tenant:{ctx.tenant_id}:{key}"
    
    async def get(self, ctx: TenantContext, key: str) -> str | None:
        return await self._redis.get(self._key(ctx, key))
    
    async def set(self, ctx: TenantContext, key: str, value: str, ttl: int | None = None) -> None:
        await self._redis.set(self._key(ctx, key), value, ex=ttl)
    
    async def delete(self, ctx: TenantContext, key: str) -> None:
        await self._redis.delete(self._key(ctx, key))
    
    async def publish(self, ctx: TenantContext, channel: str, message: str) -> None:
        await self._redis.publish(self._key(ctx, channel), message)
```

### 1.4 — Atualizar BaseModuleConfig

**Arquivo:** `intellicare_core/config/base.py` (MODIFICAR)

```diff
 class BaseModuleConfig(BaseSettings):
     module_name: str = "intellicare-module"
     module_version: str = "0.0.0"
     environment: Environment = Environment.DEVELOPMENT
     log_level: LogLevel = LogLevel.INFO
     fhir_server_url: str = "http://localhost:8080/fhir"
     fhir_timeout_seconds: int = 30
     database_url: str = ""
     redis_url: str = "redis://localhost:6379"
+    multi_tenant_enabled: bool = False
+    default_tenant_id: str = "default"
```

### 1.5 — Atualizar OperationalDataAccess

**Arquivo:** `intellicare_core/data_access/operational.py` (MODIFICAR)

O `OperationalDataAccess` já recebe `schema` como parâmetro. A mudança é fazer o schema vir do `TenantContext`:

```diff
 class OperationalDataAccess:
     def __init__(
         self,
         session: Session,
         entity_class: type[T],
         schema: str,
+        tenant_ctx: TenantContext | None = None,
         publish_event_callback: Optional[callable] = None,
     ):
+        # Se tenant_ctx for fornecido, usa o schema do tenant
+        if tenant_ctx and tenant_ctx.tenant_id != "default":
+            schema = f"{tenant_ctx.tenant_schema}_{schema}"
         self._schema = schema
         self._validate_schema()
```

### 1.6 — Logging com TenantContext

**Arquivo:** `intellicare_core/logging/tenant_filter.py` (NOVO)

```python
import logging
from contextvars import ContextVar

_tenant_var: ContextVar[str] = ContextVar("tenant_id", default="default")

class TenantLogFilter(logging.Filter):
    def filter(self, record):
        record.tenant_id = _tenant_var.get("default")
        return True

def set_tenant_for_logging(tenant_id: str):
    _tenant_var.set(tenant_id)
```

**Format de log:**
```
%(asctime)s [%(tenant_id)s] %(name)s %(levelname)s: %(message)s
```

---

## 2. Alterações em `intellicare-auth`

### 2.1 — TenantMiddleware (NOVO)

**Arquivo:** `intellicare_auth/tenant_middleware.py`

```python
from fastapi import Depends, HTTPException, status, Request
from intellicare_auth.middleware import get_current_user
from intellicare_core.tenant.context import TenantContext


async def get_tenant_context(
    request: Request,
    user: dict = Depends(get_current_user),
) -> TenantContext:
    """
    Dependency FastAPI que extrai TenantContext do JWT.
    
    Suporta 3 cenários:
    1. tenant_id presente → fluxo normal
    2. tenants[] presente mas tenant_id ausente → HTTP 428 (precisa selecionar)
    3. Nenhum dos dois → HTTP 403
    """
    tenant_id = user.get("tenant_id")
    tenants = user.get("tenants", [])
    
    # Cenário 3: nenhuma informação de tenant
    if not tenant_id and not tenants:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Token não contém informação de tenant. Acesso negado.",
        )
    
    # Cenário 2: multi-org, mas tenant não selecionado ainda
    if not tenant_id and tenants:
        raise HTTPException(
            status_code=428,  # Precondition Required
            detail={
                "error": "tenant_not_selected",
                "message": "Selecione uma organização para continuar.",
                "available_tenants": tenants,
            },
        )
    
    # Cenário 1: tenant selecionado
    ctx = TenantContext.from_jwt(user)
    
    # Armazenar no request para uso em middlewares downstream
    request.state.tenant_context = ctx
    
    return ctx


async def get_available_tenants(
    user: dict = Depends(get_current_user),
) -> list[str]:
    """Retorna lista de tenants disponíveis para o usuário (para tela de seleção)."""
    return user.get("tenants", [])


async def get_optional_tenant_context(
    request: Request,
    user: dict | None = Depends(get_current_user),
) -> TenantContext | None:
    """Para endpoints que funcionam com ou sem tenant."""
    if not user or "tenant_id" not in user:
        return None
    return TenantContext.from_jwt(user)
```

### 2.2 — Exportar no `__init__.py`

**Arquivo:** `intellicare_auth/__init__.py` (MODIFICAR)

```diff
 from intellicare_auth.middleware import get_current_user, get_optional_user, get_user_roles
+from intellicare_auth.tenant_middleware import get_tenant_context, get_optional_tenant_context
```

---

## 3. Alterações no Keycloak

### 3.1 — Client Mappers

Criar **dois Protocol Mappers** no realm `bemcuidar`:

**Mapper 1: `tenant_id` (tenant selecionado)**

| Configuração | Valor |
|---|---|
| Mapper Type | User Attribute |
| User Attribute | `tenant_id` |
| Claim Name | `tenant_id` |
| Claim JSON Type | String |
| Add to ID token | ✅ |
| Add to access token | ✅ |
| Add to userinfo | ✅ |

**Mapper 2: `tenants` (todos os tenants autorizados)**

| Configuração | Valor |
|---|---|
| Mapper Type | User Attribute |
| User Attribute | `tenants` |
| Claim Name | `tenants` |
| Claim JSON Type | JSON |
| Multivalued | ✅ |
| Add to ID token | ✅ |
| Add to access token | ✅ |
| Add to userinfo | ✅ |

### 3.2 — User Attributes

Cada usuário no Keycloak deve ter:

**Usuário single-tenant (1 hospital):**
```
User Attributes:
  tenants = ["hospital_einstein"]
  tenant_id = "hospital_einstein"     ← pré-selecionado
```

**Usuário multi-org (vários hospitais):**
```
User Attributes:
  tenants = ["hospital_einstein", "hospital_sirio", "ubs_centro"]
  tenant_id =                                      ← vazio (seleciona no Portal)
```

### 3.3 — Token Exchange SPI

Para suportar a seleção de tenant pós-login, configurar **Token Exchange** no Keycloak:

1. Habilitar Token Exchange no client `intellicare-portal`
2. Criar Custom Token Exchange Provider (SPI) que:
   - Recebe `tenant_id` no request do exchange
   - Valida que o `tenant_id` está no array `tenants` do usuário
   - Emite novo token com `tenant_id` fixo
   - Se `tenant_id` não autorizado → rejeita com 403

**Endpoint de Token Exchange:**
```
POST /realms/bemcuidar/protocol/openid-connect/token
Content-Type: application/x-www-form-urlencoded

grant_type=urn:ietf:params:oauth:grant-type:token-exchange
&subject_token={jwt_original}
&requested_token_type=urn:ietf:params:oauth:token-type:access_token
&audience=intellicare-portal
&tenant_id=hospital_sirio
```

**Resposta:**
```json
{
  "access_token": "eyJ...novo_jwt_com_tenant_id...",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

### 3.4 — Script de Configuração

**Arquivo:** `intellicare-auth/scripts/setup_tenant_mapper.py`

Script Python usando `python-keycloak` para criar os mappers automaticamente e habilitar token exchange.

---

## 4. Alterações no PostgreSQL

### 4.1 — Script de Provisionamento de Schema

**Arquivo:** `intellicare-core/scripts/provision_tenant_schema.sql`

```sql
-- Cria schema para um novo tenant
CREATE SCHEMA IF NOT EXISTS tenant_{tenant_id};

-- Copia estrutura de todas as tabelas do schema template
-- (O script de migration do Alembic deve suportar schema dinâmico)
```

### 4.2 — Alembic Multi-Schema

**Arquivo:** `intellicare-core/migrations/env.py` (MODIFICAR)

O `env.py` do Alembic deve ser capaz de rodar migrations em todos os schemas de tenant:

```python
def run_migrations_online():
    # Lista todos os schemas tenant_*
    schemas = get_all_tenant_schemas(engine)
    for schema in schemas:
        with engine.connect() as connection:
            connection.execute(text(f"SET search_path TO {schema}"))
            context.configure(connection=connection)
            context.run_migrations()
```

---

## 5. Estrutura de Arquivos (Resumo)

```
intellicare-core/
├── intellicare_core/
│   ├── tenant/                    # NOVO — Pacote de tenant
│   │   ├── __init__.py
│   │   ├── context.py             # TenantContext dataclass
│   │   ├── session.py             # TenantAwareSessionFactory
│   │   └── redis.py               # TenantRedisClient
│   ├── config/
│   │   └── base.py                # MODIFICAR — adicionar multi_tenant_enabled
│   ├── data_access/
│   │   └── operational.py         # MODIFICAR — aceitar TenantContext
│   └── logging/
│       └── tenant_filter.py       # NOVO — Log filter com tenant_id

intellicare-auth/
├── intellicare_auth/
│   ├── tenant_middleware.py       # NOVO — get_tenant_context()
│   └── __init__.py                # MODIFICAR — exportar novos symbols
├── scripts/
│   └── setup_tenant_mapper.py     # NOVO — Configura Keycloak mapper
```

---

## 6. Contratos (Interfaces Públicas)

Os seguintes contratos devem ser respeitados por **TODAS** as fases subsequentes:

```python
# 1. Obter TenantContext em qualquer endpoint
from intellicare_auth import get_tenant_context
ctx: TenantContext = Depends(get_tenant_context)

# 2. Criar session com schema do tenant
factory = TenantAwareSessionFactory(database_url)
session = await factory.get_session(ctx)

# 3. Redis com prefixo do tenant
redis = TenantRedisClient(redis_url)
await redis.set(ctx, "minha_key", "valor", ttl=3600)

# 4. Logging inclui tenant automaticamente
logger.info("Mensagem")  # Output: 2026-02-20 [hospital_einstein] ...
```
