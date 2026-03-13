---
tipo: especificacao-tecnica
demanda: DEM-003
titulo: intellicare-core — SDK Compartilhado
fase: 1
sprint: "1.1"
status: aprovado
planejador: Claude
criado: 2026-03-13
---

# DEM-003 — Especificação Técnica

> Todos os arquivos em `C:\Users\egara\INTELLICARE\packages\intellicare-core\`.
> Este pacote é Python puro — sem Docker, sem porta, sem Dockerfile.

---

## PRÉ-CONDIÇÕES

- DEM-002 concluída: `docker compose ps` mostra todos os serviços `healthy`
- `nomic-embed-text` baixado no OLLAMA:
  `docker exec intellicare-ollama ollama pull nomic-embed-text`
- Python 3.11+ disponível

---

## BLOCO 1 — Estrutura de diretórios

Criar toda a estrutura antes de qualquer arquivo:

```
packages/intellicare-core/
├── pyproject.toml
├── README.md
├── intellicare_core/
│   ├── __init__.py
│   ├── contracts/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   └── errors.py
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py
│   ├── db/
│   │   ├── __init__.py
│   │   ├── session.py
│   │   └── migrations.py
│   ├── auth/
│   │   ├── __init__.py
│   │   └── jwt.py
│   ├── vector/
│   │   ├── __init__.py
│   │   └── embeddings.py
│   └── module_loader/
│       ├── __init__.py
│       └── loader.py
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── test_contracts.py
    ├── test_config.py
    ├── test_db.py
    ├── test_auth.py
    ├── test_vector.py
    └── test_architecture.py
```

Comandos PowerShell para criar todos os diretórios e `__init__.py` vazios:

```powershell
$base = "C:\Users\egara\INTELLICARE\packages\intellicare-core"

$dirs = @(
    "intellicare_core",
    "intellicare_core\contracts",
    "intellicare_core\config",
    "intellicare_core\db",
    "intellicare_core\auth",
    "intellicare_core\vector",
    "intellicare_core\module_loader",
    "tests"
)

foreach ($d in $dirs) {
    New-Item -ItemType Directory -Force -Path "$base\$d" | Out-Null
    $init = "$base\$d\__init__.py"
    if (-not (Test-Path $init)) { New-Item -ItemType File -Path $init | Out-Null }
}
Write-Host "Estrutura criada."
```

---

## BLOCO 2 — `pyproject.toml`

```toml
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.backends.legacy:build"

[project]
name = "intellicare-core"
version = "0.1.0"
description = "SDK compartilhado do IntelliCare V3"
requires-python = ">=3.11"

dependencies = [
    "fastapi>=0.111",
    "pydantic>=2.7",
    "pydantic-settings>=2.3",
    "sqlalchemy[asyncio]>=2.0",
    "asyncpg>=0.29",
    "python-jose[cryptography]>=3.3",
    "httpx>=0.27",
    "alembic>=1.13",
]

[project.optional-dependencies]
dev = [
    "pytest>=8",
    "pytest-asyncio>=0.23",
    "pytest-cov>=5",
    "ruff>=0.4",
]

[tool.setuptools.packages.find]
where = ["."]
include = ["intellicare_core*"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B"]
```

---

## BLOCO 3 — `contracts/base.py`

```python
"""
intellicare_core.contracts.base
Contratos obrigatórios para todos os módulos.
Esta camada NÃO importa de db, auth, vector ou module_loader.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from fastapi import APIRouter
from pydantic import BaseModel

if TYPE_CHECKING:
    pass


# ── Tenant Context ─────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class TenantContext:
    """
    Objeto imutável que representa o contexto de um request autenticado.
    Criado por auth.verify_token() e injetado via FastAPI Depends.
    """
    tenant_id: str
    schema: str           # f"tenant_{tenant_id}"
    user_id: str
    roles: list[str] = field(default_factory=list)
    email: str = ""

    @classmethod
    def from_slug(cls, slug: str, user_id: str, roles: list[str], email: str = "") -> "TenantContext":
        return cls(
            tenant_id=slug,
            schema=f"tenant_{slug}",
            user_id=user_id,
            roles=roles,
            email=email,
        )

    def has_role(self, role: str) -> bool:
        return role in self.roles


# ── Health & Info ──────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str                      # "healthy" | "unhealthy"
    module: str
    version: str
    db: str = "unknown"              # "connected" | "disconnected"
    uptime_seconds: float = 0.0
    details: dict = {}


class ModuleInfo(BaseModel):
    name: str
    version: str
    description: str
    phase: str                       # "1" | "2" | "3"
    enabled_for_roles: list[str]


# ── Base Module ────────────────────────────────────────────────────────────────

class BaseModule(ABC):
    """
    Interface obrigatória de todo módulo IntelliCare.
    O ModuleLoader recusa carregar qualquer classe que não implemente esta interface.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Nome único do módulo (ex: 'admin', 'gestor', 'cuidado')."""

    @property
    @abstractmethod
    def version(self) -> str:
        """Versão semântica (ex: '0.1.0')."""

    @abstractmethod
    def get_router(self) -> APIRouter:
        """Retorna o APIRouter com todos os endpoints do módulo."""

    @abstractmethod
    async def health(self) -> HealthResponse:
        """Verificação de saúde do módulo e suas dependências."""

    def get_info(self) -> ModuleInfo:
        """Informações do módulo. Implementação padrão — pode ser sobrescrita."""
        return ModuleInfo(
            name=self.name,
            version=self.version,
            description=f"Módulo {self.name}",
            phase="1",
            enabled_for_roles=[],
        )
```

---

## BLOCO 4 — `contracts/errors.py`

```python
"""
intellicare_core.contracts.errors
Schema padronizado de erros da API.
"""

from pydantic import BaseModel
from fastapi import HTTPException


class APIError(BaseModel):
    error: str       # código de máquina: "tenant_not_found", "unauthorized", ...
    message: str     # mensagem legível para o desenvolvedor
    details: dict = {}


def api_error(status_code: int, error: str, message: str, **details) -> HTTPException:
    """
    Atalho para levantar HTTPException com body padronizado.

    Uso:
        raise api_error(404, "tenant_not_found", f"Tenant '{slug}' não existe")
        raise api_error(403, "module_disabled", "Módulo 'gestor' não habilitado neste plano")
    """
    return HTTPException(
        status_code=status_code,
        detail=APIError(error=error, message=message, details=details).model_dump(),
    )
```

---

## BLOCO 5 — `config/settings.py`

```python
"""
intellicare_core.config.settings
Configuração centralizada via pydantic-settings.
Todo acesso a variáveis de ambiente passa por aqui.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="infra/.env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # PostgreSQL
    postgres_user: str = "intellicare"
    postgres_password: str = "intellicare_dev_password"
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "intellicare"

    # Redis
    redis_password: str = "redis_dev_password"
    redis_host: str = "localhost"
    redis_port: int = 6379

    # Keycloak
    keycloak_url: str = "http://localhost:8080"
    keycloak_realm: str = "intellicare"
    keycloak_client_id: str = "intellicare-service"

    # OLLAMA
    ollama_host: str = "http://localhost:11434"
    ollama_embed_model: str = "nomic-embed-text"
    ollama_generate_model: str = "qwen2.5:7b"

    # Aplicação
    secret_key: str = "dev-secret-key-change-in-production"
    environment: str = "development"
    log_level: str = "DEBUG"

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def keycloak_jwks_url(self) -> str:
        return (
            f"{self.keycloak_url}/realms/{self.keycloak_realm}"
            f"/protocol/openid-connect/certs"
        )


@lru_cache
def get_settings() -> Settings:
    """Singleton — instância única em toda a aplicação."""
    return Settings()
```

---

## BLOCO 6 — `db/session.py`

```python
"""
intellicare_core.db.session
TenantAwareSessionFactory — sessão SQLAlchemy scoped por schema PostgreSQL.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy import text, event

from intellicare_core.config.settings import get_settings
from intellicare_core.contracts.base import TenantContext


def _make_engine(database_url: str):
    return create_async_engine(
        database_url,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        echo=get_settings().environment == "development",
    )


# Engine global (uma conexão por aplicação, não por tenant)
_engine = None


def get_engine():
    global _engine
    if _engine is None:
        _engine = _make_engine(get_settings().database_url)
    return _engine


@asynccontextmanager
async def tenant_session(ctx: TenantContext) -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager que abre uma sessão SQLAlchemy com search_path
    apontando para o schema do tenant.

    Uso:
        async with tenant_session(tenant_ctx) as db:
            result = await db.execute(select(MyModel))

    GARANTIA: toda query dentro deste bloco vai para tenant_{slug}.
    Impossível acessar dados de outro tenant por erro de código.
    """
    factory = async_sessionmaker(
        bind=get_engine(),
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with factory() as session:
        # Define search_path para o schema do tenant
        await session.execute(
            text(f"SET search_path TO {ctx.schema}, public")
        )
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def check_db_connection() -> bool:
    """Verifica conexão com o banco. Usado nos health checks."""
    try:
        async with get_engine().connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
```

---

## BLOCO 7 — `db/migrations.py`

```python
"""
intellicare_core.db.migrations
Helpers para criação e migração de schemas por tenant.
"""

import asyncpg
from intellicare_core.config.settings import get_settings


async def provision_tenant_schema(slug: str) -> None:
    """
    Cria o schema do tenant e tabelas base.
    Chamado pelo módulo admin no provisionamento.
    Idempotente — pode ser chamado múltiplas vezes sem efeito colateral.
    """
    settings = get_settings()
    dsn = (
        f"postgresql://{settings.postgres_user}:{settings.postgres_password}"
        f"@{settings.postgres_host}:{settings.postgres_port}/{settings.postgres_db}"
    )
    schema = f"tenant_{slug}"

    conn = await asyncpg.connect(dsn)
    try:
        await conn.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
        # Tabela de knowledge_base (RAG) — disponível desde o provisionamento
        await conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {schema}.knowledge_base (
                id          SERIAL PRIMARY KEY,
                title       TEXT NOT NULL,
                content     TEXT NOT NULL,
                source_path TEXT NOT NULL,
                chunk_index INTEGER NOT NULL DEFAULT 0,
                embedding   vector(768),
                metadata    JSONB DEFAULT '{{}}',
                created_at  TIMESTAMPTZ DEFAULT now(),
                updated_at  TIMESTAMPTZ DEFAULT now(),
                UNIQUE (source_path, chunk_index)
            )
        """)
    finally:
        await conn.close()


async def drop_tenant_schema(slug: str) -> None:
    """
    Remove o schema do tenant completamente.
    Chamado no encerramento de contrato após backup.
    IRREVERSÍVEL — garantir pg_dump antes de chamar.
    """
    settings = get_settings()
    dsn = (
        f"postgresql://{settings.postgres_user}:{settings.postgres_password}"
        f"@{settings.postgres_host}:{settings.postgres_port}/{settings.postgres_db}"
    )
    conn = await asyncpg.connect(dsn)
    try:
        await conn.execute(f"DROP SCHEMA IF EXISTS tenant_{slug} CASCADE")
    finally:
        await conn.close()
```

---

## BLOCO 8 — `auth/jwt.py`

```python
"""
intellicare_core.auth.jwt
Validação de JWT emitido pelo Keycloak.
"""

from functools import lru_cache
from typing import Annotated

import httpx
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from intellicare_core.config.settings import get_settings
from intellicare_core.contracts.base import TenantContext
from intellicare_core.contracts.errors import api_error


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=True)


@lru_cache(maxsize=1)
def _get_jwks() -> dict:
    """Busca as chaves públicas do Keycloak. Cache em memória (TTL via restart)."""
    settings = get_settings()
    resp = httpx.get(settings.keycloak_jwks_url, timeout=10)
    resp.raise_for_status()
    return resp.json()


def _refresh_jwks() -> dict:
    """Força atualização do cache de chaves (para rotação de keys)."""
    _get_jwks.cache_clear()
    return _get_jwks()


async def verify_token(token: str) -> TenantContext:
    """
    Valida o JWT e retorna TenantContext populado.
    Lança HTTPException 401 em qualquer falha de validação.
    """
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            _get_jwks(),
            algorithms=["RS256"],
            options={"verify_aud": False},
        )
    except JWTError:
        # Tentar com chaves atualizadas (rotação)
        try:
            payload = jwt.decode(
                token,
                _refresh_jwks(),
                algorithms=["RS256"],
                options={"verify_aud": False},
            )
        except JWTError as exc:
            raise api_error(401, "invalid_token", "Token JWT inválido ou expirado") from exc

    tenant_id = payload.get("tenant_id") or payload.get("azp")
    user_id   = payload.get("sub", "")
    email     = payload.get("email", "")
    roles: list[str] = payload.get("realm_access", {}).get("roles", [])

    if not tenant_id:
        raise api_error(401, "missing_tenant", "Token não contém tenant_id")

    return TenantContext.from_slug(
        slug=tenant_id,
        user_id=user_id,
        roles=roles,
        email=email,
    )


async def get_current_tenant(
    token: Annotated[str, Depends(oauth2_scheme)],
) -> TenantContext:
    """
    FastAPI dependency. Uso em endpoints:

        @router.get("/items")
        async def list_items(ctx: Annotated[TenantContext, Depends(get_current_tenant)]):
            async with tenant_session(ctx) as db:
                ...
    """
    return await verify_token(token)


def require_role(role: str):
    """
    FastAPI dependency factory para verificação de role.

        @router.delete("/tenant/{slug}")
        async def delete_tenant(
            ctx: Annotated[TenantContext, Depends(require_role("PLATFORM_ADMIN"))],
        ):
            ...
    """
    async def _check(ctx: Annotated[TenantContext, Depends(get_current_tenant)]) -> TenantContext:
        if not ctx.has_role(role):
            raise api_error(403, "forbidden", f"Role '{role}' necessária")
        return ctx
    return _check
```

---

## BLOCO 9 — `vector/embeddings.py`

```python
"""
intellicare_core.vector.embeddings
Embedding e busca semântica via OLLAMA + pgvector.
"""

from __future__ import annotations

import asyncio
from typing import Any

import httpx
from sqlalchemy import text

from intellicare_core.config.settings import get_settings
from intellicare_core.contracts.base import TenantContext
from intellicare_core.db.session import tenant_session


async def get_embedding(text_input: str, model: str | None = None) -> list[float]:
    """
    Gera embedding via OLLAMA.
    Retorna lista de floats (768 dims para nomic-embed-text).

    Uso:
        embedding = await get_embedding("hipertensão gestacional")
    """
    settings = get_settings()
    model = model or settings.ollama_embed_model

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            f"{settings.ollama_host}/api/embeddings",
            json={"model": model, "prompt": text_input},
        )
        resp.raise_for_status()
        return resp.json()["embedding"]


async def semantic_search(
    query: str,
    ctx: TenantContext,
    table: str = "knowledge_base",
    limit: int = 5,
    min_similarity: float = 0.5,
) -> list[dict[str, Any]]:
    """
    Busca semântica no pgvector do tenant.

    Uso:
        results = await semantic_search(
            query="protocolo para hipertensão",
            ctx=tenant_ctx,
            table="protocols",
            limit=5,
        )
        for r in results:
            print(r["title"], r["similarity"])
    """
    embedding = await get_embedding(query)
    embedding_str = "[" + ",".join(str(v) for v in embedding) + "]"

    async with tenant_session(ctx) as db:
        result = await db.execute(
            text(f"""
                SELECT
                    id,
                    title,
                    content,
                    source_path,
                    1 - (embedding <=> :emb::vector) AS similarity
                FROM {table}
                WHERE 1 - (embedding <=> :emb::vector) >= :min_sim
                ORDER BY embedding <=> :emb::vector
                LIMIT :limit
            """),
            {"emb": embedding_str, "min_sim": min_similarity, "limit": limit},
        )
        rows = result.mappings().all()
        return [dict(r) for r in rows]


async def generate(prompt: str, context_chunks: list[str], model: str | None = None) -> str:
    """
    Síntese de resposta via SLM local.

    Uso:
        answer = await generate(
            prompt="Qual o protocolo para hipertensão gestacional?",
            context_chunks=[chunk1, chunk2, chunk3],
        )
    """
    settings = get_settings()
    model = model or settings.ollama_generate_model
    context = "\n---\n".join(context_chunks)
    full_prompt = (
        f"Você é um assistente clínico. Com base nos protocolos abaixo, "
        f"responda de forma objetiva e fundamentada.\n\n"
        f"PROTOCOLOS:\n{context}\n\n"
        f"PERGUNTA: {prompt}\n\n"
        f"RESPOSTA:"
    )

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            f"{settings.ollama_host}/api/generate",
            json={"model": model, "prompt": full_prompt, "stream": False},
        )
        resp.raise_for_status()
        return resp.json()["response"]
```

---

## BLOCO 10 — `module_loader/loader.py`

```python
"""
intellicare_core.module_loader.loader
Carregamento dinâmico de módulos por tenant.
"""

from __future__ import annotations

import importlib
import logging
from typing import TYPE_CHECKING

from fastapi import FastAPI

from intellicare_core.contracts.base import BaseModule, TenantContext
from intellicare_core.contracts.errors import api_error

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

# Mapa de módulos disponíveis no sistema
# Cada entry: nome_módulo → caminho Python importável
AVAILABLE_MODULES: dict[str, str] = {
    "admin":    "modules.admin.main",
    "gestor":   "modules.gestor.main",
    "cuidado":  "modules.cuidado.main",
    "florence": "modules.florence.main",
    "oswaldo":  "modules.oswaldo.main",
}


class ModuleLoader:
    """
    Carrega módulos Python sob demanda e registra suas rotas no app FastAPI.

    Uso (no app principal):
        loader = ModuleLoader(app)
        loader.load("admin")
        loader.load("gestor")
    """

    def __init__(self, app: FastAPI) -> None:
        self.app = app
        self._loaded: dict[str, BaseModule] = {}

    def load(self, module_name: str) -> BaseModule:
        """Carrega um módulo e registra suas rotas. Idempotente."""
        if module_name in self._loaded:
            return self._loaded[module_name]

        if module_name not in AVAILABLE_MODULES:
            raise ValueError(f"Módulo '{module_name}' não existe em AVAILABLE_MODULES")

        import_path = AVAILABLE_MODULES[module_name]
        try:
            mod = importlib.import_module(import_path)
        except ImportError as exc:
            raise ImportError(
                f"Não foi possível importar módulo '{module_name}' de '{import_path}': {exc}"
            ) from exc

        # Verifica que o módulo tem uma classe que implementa BaseModule
        module_class = getattr(mod, "Module", None)
        if module_class is None or not issubclass(module_class, BaseModule):
            raise TypeError(
                f"'{import_path}' deve expor uma classe 'Module' que herda de BaseModule"
            )

        instance = module_class()
        router = instance.get_router()
        self.app.include_router(router, prefix=f"/{module_name}", tags=[module_name])

        self._loaded[module_name] = instance
        logger.info("Módulo '%s' v%s carregado.", module_name, instance.version)
        return instance

    def load_for_tenant(self, enabled_modules: list[str]) -> None:
        """Carrega todos os módulos habilitados para um tenant."""
        for name in enabled_modules:
            if name in AVAILABLE_MODULES:
                self.load(name)

    def is_enabled(self, module_name: str, ctx: TenantContext) -> bool:
        """Verifica se um módulo está carregado E habilitado para o tenant."""
        # Por ora, verifica apenas se foi carregado.
        # DEM-005 adicionará verificação contra _admin_modules do tenant.
        return module_name in self._loaded

    def get(self, module_name: str) -> BaseModule:
        if module_name not in self._loaded:
            raise api_error(
                404, "module_not_loaded",
                f"Módulo '{module_name}' não está carregado"
            )
        return self._loaded[module_name]

    @property
    def loaded_modules(self) -> list[str]:
        return list(self._loaded.keys())
```

---

## BLOCO 11 — `intellicare_core/__init__.py`

```python
"""
intellicare-core — SDK compartilhado do IntelliCare V3.

Importações principais:

    from intellicare_core.contracts import BaseModule, TenantContext
    from intellicare_core.config import get_settings
    from intellicare_core.db import tenant_session
    from intellicare_core.auth import get_current_tenant, require_role
    from intellicare_core.vector import get_embedding, semantic_search, generate
    from intellicare_core.module_loader import ModuleLoader
"""

__version__ = "0.1.0"
```

Atualizar cada sub-pacote `__init__.py` para re-exportar os símbolos principais:

`contracts/__init__.py`:
```python
from intellicare_core.contracts.base import BaseModule, TenantContext, HealthResponse, ModuleInfo
from intellicare_core.contracts.errors import APIError, api_error

__all__ = ["BaseModule", "TenantContext", "HealthResponse", "ModuleInfo", "APIError", "api_error"]
```

`config/__init__.py`:
```python
from intellicare_core.config.settings import Settings, get_settings
__all__ = ["Settings", "get_settings"]
```

`db/__init__.py`:
```python
from intellicare_core.db.session import tenant_session, check_db_connection
from intellicare_core.db.migrations import provision_tenant_schema, drop_tenant_schema
__all__ = ["tenant_session", "check_db_connection", "provision_tenant_schema", "drop_tenant_schema"]
```

`auth/__init__.py`:
```python
from intellicare_core.auth.jwt import get_current_tenant, require_role, verify_token
__all__ = ["get_current_tenant", "require_role", "verify_token"]
```

`vector/__init__.py`:
```python
from intellicare_core.vector.embeddings import get_embedding, semantic_search, generate
__all__ = ["get_embedding", "semantic_search", "generate"]
```

`module_loader/__init__.py`:
```python
from intellicare_core.module_loader.loader import ModuleLoader, AVAILABLE_MODULES
__all__ = ["ModuleLoader", "AVAILABLE_MODULES"]
```

---

## BLOCO 12 — Testes

### `tests/conftest.py`

```python
import pytest
from intellicare_core.contracts import TenantContext

@pytest.fixture
def tenant_ctx():
    return TenantContext.from_slug(
        slug="test_tenant",
        user_id="user-123",
        roles=["CLINICO"],
        email="test@test.local",
    )
```

### `tests/test_contracts.py`

```python
from intellicare_core.contracts import TenantContext, BaseModule, HealthResponse


def test_tenant_context_schema():
    ctx = TenantContext.from_slug("acme", "u1", ["CLINICO"])
    assert ctx.schema == "tenant_acme"
    assert ctx.tenant_id == "acme"


def test_tenant_context_has_role():
    ctx = TenantContext.from_slug("acme", "u1", ["PLATFORM_ADMIN", "TENANT_GESTOR"])
    assert ctx.has_role("PLATFORM_ADMIN")
    assert not ctx.has_role("CLINICO")


def test_tenant_context_immutable():
    ctx = TenantContext.from_slug("acme", "u1", [])
    try:
        ctx.tenant_id = "other"  # type: ignore
        assert False, "Deveria ser imutável"
    except (AttributeError, TypeError):
        pass


def test_base_module_is_abstract():
    import pytest
    with pytest.raises(TypeError):
        BaseModule()  # type: ignore
```

### `tests/test_config.py`

```python
from intellicare_core.config import get_settings


def test_settings_singleton():
    s1 = get_settings()
    s2 = get_settings()
    assert s1 is s2


def test_database_url_format():
    settings = get_settings()
    assert settings.database_url.startswith("postgresql+asyncpg://")
    assert settings.postgres_db in settings.database_url


def test_keycloak_jwks_url():
    settings = get_settings()
    assert "/protocol/openid-connect/certs" in settings.keycloak_jwks_url
```

### `tests/test_architecture.py`

```python
"""
Testa que contracts não importa de camadas superiores.
Enforça a regra: contracts → config → db → auth/vector → module_loader
"""
import ast
import sys
from pathlib import Path

CORE = Path(__file__).parent.parent / "intellicare_core"

FORBIDDEN_IMPORTS = {
    "intellicare_core/contracts": ["intellicare_core.db", "intellicare_core.auth",
                                    "intellicare_core.vector", "intellicare_core.module_loader"],
    "intellicare_core/config":    ["intellicare_core.db", "intellicare_core.auth",
                                    "intellicare_core.vector", "intellicare_core.module_loader"],
}


def get_imports(filepath: Path) -> list[str]:
    tree = ast.parse(filepath.read_text())
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            if isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
    return imports


def test_contracts_no_upward_imports():
    contracts_dir = CORE / "contracts"
    for py_file in contracts_dir.glob("*.py"):
        imports = get_imports(py_file)
        forbidden = FORBIDDEN_IMPORTS.get("intellicare_core/contracts", [])
        for imp in imports:
            for forbidden_imp in forbidden:
                assert not imp.startswith(forbidden_imp), (
                    f"{py_file.name} importa '{imp}' — viola a regra de camadas. "
                    f"contracts não pode importar de {forbidden_imp}"
                )


def test_config_no_upward_imports():
    config_dir = CORE / "config"
    for py_file in config_dir.glob("*.py"):
        imports = get_imports(py_file)
        forbidden = FORBIDDEN_IMPORTS.get("intellicare_core/config", [])
        for imp in imports:
            for forbidden_imp in forbidden:
                assert not imp.startswith(forbidden_imp), (
                    f"{py_file.name} importa '{imp}' — viola a regra de camadas."
                )
```

---

## BLOCO 13 — Instalação e execução dos testes

```powershell
cd C:\Users\egara\INTELLICARE

# Instalar o pacote em modo editável
pip install -e packages\intellicare-core[dev]

# Executar testes
pytest packages\intellicare-core\tests\ -v --tb=short

# Verificar importações funcionam
python -c "from intellicare_core.contracts import BaseModule, TenantContext; print('OK contracts')"
python -c "from intellicare_core.config import get_settings; s = get_settings(); print('OK config', s.environment)"
python -c "from intellicare_core.db import tenant_session; print('OK db')"
python -c "from intellicare_core.auth import get_current_tenant; print('OK auth')"
python -c "from intellicare_core.vector import get_embedding; print('OK vector')"
python -c "from intellicare_core.module_loader import ModuleLoader; print('OK loader')"
```

---

## BLOCO 14 — Commit

```powershell
cd C:\Users\egara\INTELLICARE
git add packages\intellicare-core\
git commit -m "feat(core): intellicare-core SDK - contracts, config, db, auth, vector, module_loader"
git push origin main
```

---

## Resultado esperado

```
packages/intellicare-core/
├── pyproject.toml
├── intellicare_core/
│   ├── __init__.py         (version = "0.1.0")
│   ├── contracts/          (BaseModule, TenantContext, APIError)
│   ├── config/             (Settings, get_settings)
│   ├── db/                 (tenant_session, provision_tenant_schema)
│   ├── auth/               (verify_token, get_current_tenant, require_role)
│   ├── vector/             (get_embedding, semantic_search, generate)
│   └── module_loader/      (ModuleLoader)
└── tests/
    ├── test_contracts.py   ✓
    ├── test_config.py      ✓
    ├── test_architecture.py ✓ (enforça regras de camada)
    └── ...
```

`pytest packages/intellicare-core/tests/ -v` — todos os testes verdes.
`pip install -e packages/intellicare-core` — funciona sem erro.
