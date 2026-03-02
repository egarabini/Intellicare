# ESPECIFICAÇÃO TÉCNICA - IntelliCare Admin

**Data**: 2026-03-02
**Status**: 🟡 Especificação Técnica em Elaboração
**Prioridade**: 🚨 ALTA PRIORIDADE
**Rastreabilidade**: 20260302-1400_ESPECIFICACAO_FUNCIONAL.md
**Versão**: 1.0.0

---

## 📋 Índice

1. [Visão Geral Técnica](#visão-geral-técnica)
2. [Stack Tecnológico](#stack-tecnológico)
3. [Arquitetura Detalhada](#arquitetura-detalhada)
4. [API Design](#api-design)
5. [Modelo de Dados](#modelo-de-dados)
6. [Integrações](#integrações)
7. [Segurança](#segurança)
8. [Performance](#performance)
9. [Deploy](#deploy)
10. [Monitoramento](#monitoramento)

---

## 🎯 Visão Geral Técnica

### Responsabilidade do Módulo

O **intellicare-admin** é um serviço FastAPI que:

- Expõe API REST para administração da plataforma (nível PLATAFORMA)
- Gerencia **Estabelecimentos** (Hospitais, Clínicas, Laboratórios, Secretarias de Saúde)
- Gerencia **Usuários PLATAFORMA**: PLATFORM_GESTOR, PLATFORM_SUPPORT, PLATFORM_BILLING
- Orquestra provisioning de estabelecimentos
- Integra com Keycloak para gestão de identidades
- Publica métricas para Prometheus

> **NOTA**: Este módulo NÃO gerencia Unidades nem Usuários de Saúde (HEALTH_*). Isso é feito pelo **intellicare-gestor** (PORT 8011).

### Características Técnicas

- **Porta**: 8010 (HTTP)
- **Async**: AsyncIO + asyncpg (PostgreSQL)
- **Type Safety**: Python 3.11+ + Pydantic v2
- **API**: OpenAPI 3.0 (FastAPI auto-generated)
- **Auth**: Keycloak JWT (Bearer token)
- **DB**: PostgreSQL 15+ (schema: platform)

---

## 🛠️ Stack Tecnológico

### Core

| Componente | Versão | Propósito |
|------------|--------|-----------|
| **Python** | 3.11+ | Runtime |
| **FastAPI** | 0.109+ | Web framework |
| **Pydantic** | 2.0+ | Validação/serialização |
| **SQLAlchemy** | 2.0+ | ORM |
| **asyncpg** | 0.29+ | Async PostgreSQL driver |

### Dependências IntelliCare

| Componente | Versão | Propósito |
|------------|--------|-----------|
| **intellicare-core** | latest | TenantContext, BaseAgent, etc |
| **intellicare-auth** | latest | Keycloak integration, JWT validation |

### Infraestrutura

| Componente | Versão | Propósito |
|------------|--------|-----------|
| **PostgreSQL** | 15+ | Banco de dados |
| **Keycloak** | 24+ | Autenticação/autorização |
| **Redis** | 7+ | Cache, filas |
| **Prometheus** | latest | Métricas |

---

## 🏗️ Arquitetura Detalhada

### Estrutura de Diretórios

```
intellicare-admin/
├── admin/
│   ├── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── app.py              # FastAPI app, lifespan, middleware
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── estabelecimentos.py  # CRUD estabelecimentos
│   │   │   ├── gestores.py          # CRUD gestores (PLATFORM_GESTOR)
│   │   │   ├── plans.py             # CRUD planos
│   │   │   ├── billing.py           # Billing endpoints
│   │   │   ├── dashboard.py         # Metrics endpoint
│   │   │   ├── audit.py             # Audit log endpoints
│   │   │   └── support.py           # Impersonation
│   │   ├── deps.py              # Dependencies (auth, db)
│   │   └── middleware.py        # Custom middleware
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py            # Settings, env vars
│   │   ├── security.py          # Password hashing, etc
│   │   └── tenant.py            # Tenant context helpers
│   ├── models/
│   │   ├── __init__.py
│   │   ├── tenant.py            # ORM models
│   │   ├── plan.py
│   │   ├── billing.py
│   │   └── audit.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── tenant.py            # Pydantic schemas (req/res)
│   │   ├── plan.py
│   │   ├── billing.py
│   │   └── audit.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── tenant_service.py    # Business logic
│   │   ├── provisioning.py      # Provisioning orchestration
│   │   ├── billing_service.py
│   │   └── audit_service.py
│   ├── workers/
│   │   ├── __init__.py
│   │   └── provisioning_worker.py  # Background provisioning
│   ├── tasks/
│   │   ├── __init__.py
│   │   └── billing_tasks.py     # Celery/background tasks
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── cnpj.py              # CNPJ validation
│   │   ├── email.py             # Email templates
│   │   └── metrics.py           # Prometheus metrics
│   └── db.py                    # Database engine, session
├── tests/
│   ├── api/
│   ├── services/
│   └── conftest.py
├── migrations/                  # Alembic
│   ├── versions/
│   └── env.py
├── alembic.ini
├── pyproject.toml
├── Dockerfile
├── docker-compose.yml
└── README.md
```

### Camadas da Aplicação

```
┌─────────────────────────────────────────────────────────┐
│  API Layer (FastAPI Router)                              │
│  /api/v1/admin/*                                         │
├─────────────────────────────────────────────────────────┤
│  Middleware Layer                                        │
│  - JWT validation (PLATFORM_ADMIN)                       │
│  - Tenant context (platform)                             │
│  - Request logging                                       │
├─────────────────────────────────────────────────────────┤
│  Service Layer (Business Logic)                          │
│  - TenantService                                         │
│  - ProvisioningService                                   │
│  - BillingService                                        │
│  - AuditService                                          │
├─────────────────────────────────────────────────────────┤
│  Repository Layer (Data Access)                          │
│  - SQLAlchemy ORM                                        │
│  - Async session management                              │
├─────────────────────────────────────────────────────────┤
│  Integration Layer                                       │
│  - Keycloak Admin API                                    │
│  - Redis (cache, queues)                                 │
│  - SMTP (emails)                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 🌐 API Design

### Autenticação

Todos os endpoints requerem **Bearer Token** JWT do Keycloak com a role `PLATFORM_ADMIN`:

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Response Format

**Success** (200-299):
```json
{
  "data": { ... },
  "meta": {
    "timestamp": "2026-03-02T14:00:00Z",
    "request_id": "uuid"
  }
}
```

**Error** (400-599):
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "CNPJ inválido",
    "details": { ... }
  },
  "meta": {
    "timestamp": "2026-03-02T14:00:00Z",
    "request_id": "uuid"
  }
}
```

### Endpoints Principais

#### Estabelecimentos

```
POST   /api/v1/admin/estabelecimentos                    Criar estabelecimento
GET    /api/v1/admin/estabelecimentos                    Listar estabelecimentos (paginado)
GET    /api/v1/admin/estabelecimentos/{id}               Detalhes do estabelecimento
PATCH  /api/v1/admin/estabelecimentos/{id}               Atualizar estabelecimento
DELETE /api/v1/admin/estabelecimentos/{id}               Excluir estabelecimento (soft delete)
POST   /api/v1/admin/estabelecimentos/{id}/suspender     Suspender estabelecimento
POST   /api/v1/admin/estabelecimentos/{id}/reativar     Reativar estabelecimento
GET    /api/v1/admin/estabelecimentos/{id}/modulos      Módulos do estabelecimento
PATCH  /api/v1/admin/estabelecimentos/{id}/modulos      Atualizar módulos
```

#### Gestores (PLATFORM_GESTOR)

```
POST   /api/v1/admin/estabelecimentos/{id}/gestores     Criar gestor
GET    /api/v1/admin/estabelecimentos/{id}/gestores     Listar gestores
PATCH  /api/v1/admin/gestores/{id}                       Atualizar gestor
DELETE /api/v1/admin/gestores/{id}                      Remover gestor
```

#### Plans

```
GET    /api/v1/admin/plans                      Listar planos
POST   /api/v1/admin/plans                      Criar plano (super-admin only)
GET    /api/v1/admin/plans/{id}                 Detalhes do plano
PATCH  /api/v1/admin/plans/{id}                 Atualizar plano
```

#### Billing

```
GET    /api/v1/admin/billing/records            Registros de billing
GET    /api/v1/admin/billing/tenants/{id}       Billing por tenant
POST   /api/v1/admin/billing/tenants/{id}/pay   Registrar pagamento
```

#### Dashboard

```
GET    /api/v1/admin/dashboard/metrics          Métricas globais
GET    /api/v1/admin/dashboard/tenants          Top N tenants por uso
```

#### Audit

```
GET    /api/v1/admin/audit/logs                Logs de auditoria (paginated)
GET    /api/v1/admin/audit/logs/{id}            Detalhes do log
```

#### Support

```
POST   /api/v1/admin/support/impersonate        Impersonar tenant
GET    /api/v1/admin/support/sessions           Sessões ativas
DELETE /api/v1/admin/support/sessions/{id}      Encerrar sessão
```

### Exemplo: Criar Estabelecimento

**Request**:
```http
POST /api/v1/admin/estabelecimentos HTTP/1.1
Host: admin.intellicare.ia.br
Authorization: Bearer eyJhbG...
Content-Type: application/json

{
  "nome": "Hospital Santa Clara",
  "cnes": "1234567",
  "cnpj": "12.345.678/0001-90",
  "tipo": "HOSPITAL",
  "gestor": {
    "nome": "Maria Silva",
    "email": "maria.santaclara@email.com",
    "telefone": "+5511999999999"
  },
  "plano_id": "professional",
  "modulos": ["florence", "oswaldo", "wanda"]
}
```

**Response** (202 Accepted):
```json
{
  "data": {
    "id": "uuid",
    "nome": "Hospital Santa Clara",
    "status": "provisioning",
    "criado_em": "2026-03-02T14:00:00Z"
  },
  "meta": {
    "message": "Estabelecimento criado. Provisionamento em andamento.",
    "provisionamento_id": "uuid"
  }
}
```

---

## 📊 Modelo de Dados

### ORM Models (SQLAlchemy 2.0)

```python
# admin/models/estabelecimento.py

from sqlalchemy import Column, String, DateTime, JSON, Integer, Boolean, Numeric, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from admin.db import Base


class Estabelecimento(Base):
    __tablename__ = "estabelecimentos"
    __table_args__ = {"schema": "platform"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome = Column(String(255), nullable=False)
    cnes = Column(String(15), unique=True)  # CNES do DATASUS
    cnpj = Column(String(14), unique=True)
    tipo = Column(String(50), nullable=False)  # HOSPITAL, CLINICA, LABORATORIO, SECRETARIA
    logo_url = Column(String(512))
    status = Column(String(50), default="provisioning")  # provisioning, active, suspended, cancelled

    # Contato do gestor principal
    gestor_nome = Column(String(255))
    gestor_email = Column(String(255))
    gestor_telefone = Column(String(20))

    # Configurações
    configuracoes = Column(JSON, default=dict)

    # Plano
    plano_id = Column(String(50), ForeignKey("platform.planos.id"))

    # Metadata
    criado_em = Column(DateTime(timezone=True), server_default=func.now())
    atualizado_em = Column(DateTime(timezone=True), onupdate=func.now())
    criado_por = Column(UUID(as_uuid=True))
    provisionado_em = Column(DateTime(timezone=True))
    suspenso_em = Column(DateTime(timezone=True))
    cancelado_em = Column(DateTime(timezone=True))

    rowversion = Column(Integer, default=1)

    # Relationships
    plano = relationship("Plano", backref="estabelecimentos")
    gestores = relationship("Gestor", back_populates="estabelecimento")


class Gestor(Base):
    __tablename__ = "gestores"
    __table_args__ = {"schema": "platform"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    estabelecimento_id = Column(UUID(as_uuid=True), ForeignKey("platform.estabelecimentos.id"))
    usuario_keycloak_id = Column(UUID(as_uuid=True), nullable=False)
    nome = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    permissoes = Column(JSON, default=dict)  # {"pode_gerenciar_usuarios": true, ...}
    ativo = Column(Boolean, default=True)

    # Metadata
    criado_em = Column(DateTime(timezone=True), server_default=func.now())
    criado_por = Column(UUID(as_uuid=True))

    # Relationship
    estabelecimento = relationship("Estabelecimento", back_populates="gestores")


class Plano(Base):
    __tablename__ = "planos"
    __table_args__ = {"schema": "platform"}

    id = Column(String(50), primary_key=True)  # trial, basico, profissional, enterprise
    nome = Column(String(255), nullable=False)
    descricao = Column(Text)
    preco_mensal = Column(Numeric(10, 2))
    moeda = Column(String(3), default="BRL")

    # Limites
    max_gestores = Column(Integer)
    max_usuarios_saude = Column(Integer)
    max_storage_gb = Column(Integer)
    max_chamadas_api_mensal = Column(Integer)

    # Módulos incluídos
    modulos = Column(JSON, default=list)  # ["florence", "oswaldo", "wanda"]

    status = Column(String(50), default="active")
    criado_em = Column(DateTime(timezone=True), server_default=func.now())


class ModuloPorEstabelecimento(Base):
    __tablename__ = "modulos_por_estabelecimento"
    __table_args__ = {"schema": "platform"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    estabelecimento_id = Column(UUID(as_uuid=True), ForeignKey("platform.estabelecimentos.id"))
    nome_modulo = Column(String(100), nullable=False)
    habilitado = Column(Boolean, default=True)
    configuracao = Column(JSON, default=dict)

    estabelecimento = relationship("Estabelecimento", backref="modulos")
    __table_args__ = (
        UniqueConstraint("estabelecimento_id", "nome_modulo"),
    )


class RegistroBilling(Base):
    __tablename__ = "registros_billing"
    __table_args__ = {"schema": "platform"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    estabelecimento_id = Column(UUID(as_uuid=True), ForeignKey("platform.estabelecimentos.id"))
    periodo_ano = Column(Integer, nullable=False)
    periodo_mes = Column(Integer, nullable=False)

    # Uso
    gestores_ativos = Column(Integer, default=0)
    usuarios_saude_ativos = Column(Integer, default=0)
    chamadas_api = Column(Integer, default=0)
    storage_gb = Column(Numeric(10, 2), default=0)

    # Valores
    preco_base = Column(Numeric(10, 2))
    preco_excedente = Column(Numeric(10, 2), default=0)
    preco_total = Column(Numeric(10, 2))

    # Status
    status = Column(String(50), default="pending")  # pending, paid, overdue, cancelled
    pago_em = Column(DateTime(timezone=True))
    data_vencimento = Column(Date)

    criado_em = Column(DateTime(timezone=True), server_default=func.now())

    estabelecimento = relationship("Estabelecimento", backref="registros_billing")
    __table_args__ = (
        UniqueConstraint("estabelecimento_id", "periodo_ano", "periodo_mes"),
    )


class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = {"schema": "platform"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    actor_id = Column(UUID(as_uuid=True), nullable=False)
    actor_email = Column(String(255), nullable=False)
    actor_role = Column(String(100), nullable=False)

    action = Column(String(100), nullable=False)
    target_type = Column(String(50))
    target_id = Column(UUID(as_uuid=True))

    payload = Column(JSON)
    result = Column(String(50))
    error_message = Column(Text)

    ip = Column(String(45))
    user_agent = Column(Text)

    impersonated_as = Column(UUID(as_uuid=True))
    reason = Column(Text)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

### Pydantic Schemas

```python
# admin/schemas/estabelecimento.py

from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from uuid import UUID
from typing import Optional, List
import re


class EstabelecimentoCreate(BaseModel):
    nome: str = Field(..., min_length=3, max_length=255)
    cnes: Optional[str] = Field(None, min_length=7, max_length=15)
    cnpj: str = Field(..., pattern=r"^\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}$")
    tipo: str = Field(..., min_length=3, max_length=50)  # HOSPITAL, CLINICA, LABORATORIO, SECRETARIA
    gestor: Optional[dict] = None  # {"nome": "...", "email": "...", "telefone": "..."}
    plano_id: str = Field(..., min_length=3, max_length=50)
    modulos: List[str] = Field(default_factory=list)

    @field_validator("cnpj")
    @classmethod
    def validate_cnpj(cls, v: str) -> str:
        # Remove formatação e valida dígitos
        numbers = re.sub(r"[^\d]", "", v)
        if not validate_cnpj_digits(numbers):
            raise ValueError("CNPJ inválido")
        return numbers


class EstabelecimentoResponse(BaseModel):
    id: UUID
    nome: str
    cnes: Optional[str]
    cnpj: Optional[str]
    tipo: str
    logo_url: Optional[str]
    status: str
    plano_id: Optional[str]
    gestor_nome: Optional[str]
    gestor_email: Optional[str]
    gestor_telefone: Optional[str]
    criado_em: datetime
    provisionado_em: Optional[datetime]

    class Config:
        from_attributes = True


class EstabelecimentoUpdate(BaseModel):
    nome: Optional[str] = Field(None, min_length=3, max_length=255)
    logo_url: Optional[str] = None
    gestor_email: Optional[str] = Field(None, email=True)
    gestor_telefone: Optional[str] = None
    configuracoes: Optional[dict] = None


class EstabelecimentoListResponse(BaseModel):
    items: List[EstabelecimentoResponse]
    total: int
    page: int
    per_page: int


# Gestor schemas
class GestorCreate(BaseModel):
    nome: str = Field(..., min_length=3, max_length=255)
    email: str = Field(..., email=True)
    permissoes: Optional[dict] = None


class GestorResponse(BaseModel):
    id: UUID
    estabelecimento_id: UUID
    nome: str
    email: str
    permissoes: dict
    ativo: bool
    criado_em: datetime

    class Config:
        from_attributes = True
```

---

## 🔌 Integrações

### Keycloak Admin API

```python
# admin/services/keycloak_service.py

from python_keycloak import KeycloakAdmin
from admin.core.config import settings

class KeycloakService:
    def __init__(self):
        self.admin = KeycloakAdmin(
            server_url=settings.keycloak_url,
            username=settings.keycloak_username,
            password=settings.keycloak_password,
            realm_name=settings.keycloak_realm,
            verify=True
        )

    async def create_estabelecimento_group(self, estabelecimento_id: str, nome: str):
        """Cria grupo para o estabelecimento no Keycloak"""
        group_id = self.admin.create_group(
            payload={
                "name": f"estabelecimento_{estabelecimento_id}",
                "attributes": {
                    "estabelecimento_id": [estabelecimento_id],
                    "tipo": ["estabelecimento"]
                }
            }
        )
        return group_id

    async def create_gestor_user(
        self,
        estabelecimento_id: str,
        nome: str,
        email: str,
        password: str
    ):
        """Cria usuário gestor (PLATFORM_GESTOR) do estabelecimento"""
        user_id = self.admin.create_user(
            payload={
                "username": email,
                "email": email,
                "firstName": nome.split(" ")[0],
                "lastName": " ".join(nome.split(" ")[1:]),
                "enabled": True,
                "groups": [f"estabelecimento_{estabelecimento_id}"],
                "credentials": [{
                    "type": "password",
                    "value": password,
                    "temporary": True
                }],
                "attributes": {
                    "estabelecimento_id": [estabelecimento_id],
                    "role": ["PLATFORM_GESTOR"]
                }
            }
        )

        # Atribuir role PLATFORM_GESTOR
        self.admin.assign_group_role(
            user_id=user_id,
            group_id=self.get_platform_gestor_group_id(),
            role_id=self.get_platform_gestor_role_id()
        )

        return user_id

    async def revoke_estabelecimento_tokens(self, estabelecimento_id: str):
        """Revoga todos os tokens do estabelecimento (suspensão)"""
        group_id = self.admin.get_group_id(group_name=f"estabelecimento_{estabelecimento_id}")
        members = self.admin.get_group_members(group_id)

        for member in members:
            self.admin.logout_user(user_id=member["id"])
```

### PostgreSQL Schema Management

```python
# admin/services/provisioning.py

class ProvisioningService:
    async def create_estabelecimento_schema(self, estabelecimento_id: str):
        """Cria schema e tabelas base para o estabelecimento"""
        async with self.db.begin():
            # Criar schema
            await self.db.execute(f"CREATE SCHEMA IF NOT EXISTS estabelecimento_{estabelecimento_id}")

            # NOTA: As tabelas de Unidades e Usuários de Saúde serão criadas pelo
            # módulo intellicare-gestor (FASE3)
            # Aqui criamos apenas a estrutura básica do schema

            # Criar tabela de configurações básicas
            await self.db.execute(f"""
                CREATE TABLE IF NOT EXISTS estabelecimento_{estabelecimento_id}.configuracoes (
                    key VARCHAR PRIMARY KEY,
                    value JSONB NOT NULL,
                    atualizado_em TIMESTAMP DEFAULT NOW()
                )
            """)

            # Inserir config inicial
            await self.db.execute(f"""
                INSERT INTO estabelecimento_{estabelecimento_id}.configuracoes (key, value)
                VALUES ('defaults', '{"language": "pt-BR", "timezone": "America/Sao_Paulo"}')
            """)

    async def drop_estabelecimento_schema(self, estabelecimento_id: str):
        """Remove schema do estabelecimento (exclusão)"""
        await self.db.execute(f"DROP SCHEMA IF EXISTS estabelecimento_{estabelecimento_id} CASCADE")
```

### Redis (Cache e Filas)

```python
# admin/services/cache.py

import redis.asyncio as redis
from admin.core.config import settings

class CacheService:
    def __init__(self):
        self.redis = redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True
        )

    async def cache_estabelecimento(self, estabelecimento_id: str, data: dict, ttl: int = 3600):
        """Cache dados do estabelecimento"""
        await self.redis.setex(
            f"estabelecimento:{estabelecimento_id}",
            ttl,
            json.dumps(data)
        )

    async def get_cached_estabelecimento(self, estabelecimento_id: str) -> Optional[dict]:
        """Obtém estabelecimento do cache"""
        data = await self.redis.get(f"estabelecimento:{estabelecimento_id}")
        return json.loads(data) if data else None

    async def publish_provisioning_event(self, estabelecimento_id: str):
        """Publica evento de provisioning"""
        await self.redis.xadd(
            "estabelecimento.provisioning",
            {
                "estabelecimento_id": str(estabelecimento_id),
                "action": "provision",
                "timestamp": datetime.utcnow().isoformat()
            }
        )
```

---

## 🔒 Segurança

### JWT Validation Middleware

```python
# admin/api/middleware.py

from fastapi import Request, HTTPException, status
from intellicare_auth import validate_token

async def require_platform_admin(request: Request):
    """Valida JWT e requer role PLATFORM_ADMIN"""

    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header"
        )

    token = auth_header.split(" ")[1]

    try:
        payload = await validate_token(token)
        roles = payload.get("realm_access", {}).get("roles", [])

        if "PLATFORM_ADMIN" not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="PLATFORM_ADMIN role required"
            )

        # Adiciona user info ao request state
        request.state.user_id = payload.get("sub")
        request.state.user_email = payload.get("email")
        request.state.user_roles = roles

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
```

### Row-Level Security (PostgreSQL)

```sql
-- Habilitar RLS no schema platform
ALTER SCHEMA platform DEFAULT PRIVILEGES INCLUDE ALL;

-- Policy: apenas admin module pode escrever
CREATE POLICY platform_write_policy ON tenants
  FOR ALL
  TO admin_module_role
  USING (true)
  WITH CHECK (true);

-- Policy: outros módulos podem apenas ler
CREATE POLICY platform_read_policy ON tenants
  FOR SELECT
  TO tenant_module_role
  USING (true);
```

---

## ⚡ Performance

### Otimizações

1. **Índices**:
   - CNPJ único indexado
   - Domain único indexado
   - Status + created_at composto (listagens)
   - tenant_id em billing_records

2. **Cache**:
   - Detalhes de tenant (1h TTL)
   - Lista de planos (24h TTL)
   - Métricas de dashboard (5min TTL)

3. **Queries**:
   - Paginação obrigatória (max 100 itens)
   - Select específico (evitar SELECT *)
   - Join otimizados com relationship()

4. **Background Tasks**:
   - Provisionamento assíncrono (Redis queue)
   - Job de billing fora do horário comercial

### SLAs

| Operação | P50 | P95 | P99 |
|----------|-----|-----|-----|
| Criar estabelecimento | 200ms | 500ms | 1s |
| Listar estabelecimentos | 100ms | 300ms | 500ms |
| Dashboard | 200ms | 500ms | 1s |
| Provisionamento | 10s | 20s | 30s |

---

## 🚀 Deploy

### Docker Compose

```yaml
# docker-compose.admin.yml

services:
  admin:
    build:
      context: ./intellicare-admin
      dockerfile: Dockerfile
    container_name: intellicare-admin
    ports:
      - "8010:8010"
    environment:
      - DATABASE_URL=postgresql+asyncpg://user:pass@postgres:5432/intellicare
      - KEYCLOAK_URL=https://auth.intellicare.ia.br
      - KEYCLOAK_ADMIN_USERNAME=admin
      - KEYCLOAK_ADMIN_PASSWORD=${KEYCLOAK_ADMIN_PASSWORD}
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - redis
    networks:
      - intellicare-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8010/api/v1/health"]
      interval: 30s
      timeout: 5s
      retries: 3
```

### Migrations

```bash
# Aplicar migrations
alembic upgrade head

# Criar nova migration
alembic revision --autogenerate -m "description"

# Rollback
alembic downgrade -1
```

---

## 📊 Monitoramento

### Métricas Prometheus

```python
# admin/utils/metrics.py

from prometheus_client import Counter, Histogram, Gauge

# Contadores
estabelecimentos_criados_total = Counter(
    "admin_estabelecimentos_criados_total",
    "Total de estabelecimentos criados"
)

estabelecimentos_suspensos_total = Counter(
    "admin_estabelecimentos_suspensos_total",
    "Total de estabelecimentos suspensos"
)

# Histogramas
provisioning_duration_seconds = Histogram(
    "admin_provisioning_duration_seconds",
    "Duração do provisionamento"
)

api_request_duration_seconds = Histogram(
    "admin_api_request_duration_seconds",
    "Duração de requisições API",
    ["endpoint", "method", "status"]
)

# Gauges
estabelecimentos_ativos = Gauge(
    "admin_estabelecimentos_ativos",
    "Número de estabelecimentos ativos"
)

billing_overdue_total = Gauge(
    "admin_billing_overdue_total",
    "Valor total de billing em atraso"
)
```

### Health Check

```python
@router.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    db_ok = await check_database()
    redis_ok = await check_redis()
    keycloak_ok = await check_keycloak()

    return {
        "status": "healthy" if all([db_ok, redis_ok, keycloak_ok]) else "unhealthy",
        "checks": {
            "database": "ok" if db_ok else "failed",
            "redis": "ok" if redis_ok else "failed",
            "keycloak": "ok" if keycloak_ok else "failed"
        },
        "timestamp": datetime.utcnow().isoformat()
    }
```

---

## 📝 Próximos Passos

1. **Implementar**: Seguir `PASSOS_IMPLEMENTACAO.md`
2. **Testar**: Executar suite de testes
3. **Documentar**: Atualizar README.md
4. **Deploy**: Subir para staging
5. **Monitorar**: Configurar dashboards Grafana

---

**Especificação Técnica v1.0.0**
**Data**: 2026-03-02
**Responsável**: IntelliCare Team
