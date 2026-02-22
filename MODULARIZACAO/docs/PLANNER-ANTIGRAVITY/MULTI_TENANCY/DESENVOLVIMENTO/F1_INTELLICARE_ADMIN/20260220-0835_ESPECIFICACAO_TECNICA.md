# F1 — Especificação Técnica: intellicare-admin

> **Módulo:** `intellicare-admin` (NOVO)  
> **Schema:** `platform` | **Porta:** 8010  
> **Stack:** Python 3.11+, FastAPI, SQLAlchemy 2.x, Alembic, Keycloak Admin API

---

## 1. Estrutura do Módulo

```
intellicare-admin/
├── admin/
│   ├── __init__.py
│   ├── config.py                  # AdminConfig (herda BaseModuleConfig)
│   ├── models/
│   │   ├── __init__.py
│   │   ├── tenant.py              # Tenant, TenantModule ORM models
│   │   ├── plan.py                # Plan, PlanModule ORM models
│   │   ├── billing.py             # BillingRecord ORM model
│   │   └── audit.py               # GlobalAuditLog ORM model
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── tenant_schemas.py      # Pydantic request/response schemas
│   │   ├── plan_schemas.py
│   │   └── billing_schemas.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── tenant_service.py      # CRUD + business logic
│   │   ├── provisioning_service.py # Schema creation + KC + seed
│   │   ├── billing_service.py     # Billing calculations
│   │   └── impersonation_service.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── app.py                 # FastAPI create_app
│   │   ├── tenant_routes.py       # /admin/tenants/*
│   │   ├── plan_routes.py         # /admin/plans/*
│   │   ├── billing_routes.py      # /admin/billing/*
│   │   ├── dashboard_routes.py    # /admin/dashboard
│   │   └── audit_routes.py        # /admin/audit
│   └── migrations/
│       └── alembic/               # Migrations para schema "platform"
├── tests/
│   ├── test_tenant_service.py
│   ├── test_provisioning.py
│   └── test_billing.py
├── pyproject.toml
├── requirements.txt
└── README.md
```

---

## 2. Modelos ORM (SQLAlchemy)

### 2.1 — Tenant

```python
# admin/models/tenant.py
from sqlalchemy import Column, String, Boolean, DateTime, Enum, JSON, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base
import uuid
from datetime import datetime, UTC

Base = declarative_base()

class TenantStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TRIAL = "trial"
    CANCELLED = "cancelled"

class Tenant(Base):
    __tablename__ = "tenants"
    __table_args__ = {"schema": "platform"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(100), unique=True, nullable=False, index=True)  # slug
    nome_fantasia = Column(String(255), nullable=False)
    razao_social = Column(String(255), nullable=False)
    cnpj = Column(String(18), unique=True, nullable=False)
    email_admin = Column(String(255), nullable=False)
    
    # Branding
    logo_url = Column(String(500))
    cor_primaria = Column(String(7), default="#1E88E5")
    cor_secundaria = Column(String(7), default="#43A047")
    dominio_custom = Column(String(255))
    
    # Plano
    plan_id = Column(UUID(as_uuid=True), ForeignKey("platform.plans.id"))
    
    # Status
    status = Column(String(20), default="trial")
    provisioned = Column(Boolean, default=False)
    
    # Limites
    max_users = Column(Integer, default=5)
    max_sms_month = Column(Integer, default=100)
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, onupdate=lambda: datetime.now(UTC))
    trial_expires_at = Column(DateTime)
    suspended_at = Column(DateTime)


class TenantModule(Base):
    __tablename__ = "tenant_modules"
    __table_args__ = {"schema": "platform"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(100), ForeignKey("platform.tenants.tenant_id"))
    module_name = Column(String(100), nullable=False)  # "zilda", "oswaldo", etc.
    enabled = Column(Boolean, default=True)
    config_json = Column(JSON, default={})  # Config específica por tenant/módulo
    activated_at = Column(DateTime, default=lambda: datetime.now(UTC))
```

### 2.2 — Plan

```python
# admin/models/plan.py
class Plan(Base):
    __tablename__ = "plans"
    __table_args__ = {"schema": "platform"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(50), unique=True, nullable=False)  # trial, basico, etc.
    display_name = Column(String(100), nullable=False)
    max_users = Column(Integer, default=5)
    max_sms_month = Column(Integer, default=100)
    price_monthly = Column(Numeric(10, 2), default=0)
    modules_included = Column(JSON, default=[])  # ["zilda", "florence", ...]
    active = Column(Boolean, default=True)
```

### 2.3 — BillingRecord

```python
# admin/models/billing.py
class BillingRecord(Base):
    __tablename__ = "billing_records"
    __table_args__ = {"schema": "platform"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(100), ForeignKey("platform.tenants.tenant_id"))
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    plan_name = Column(String(50))
    
    # Uso
    active_users = Column(Integer, default=0)
    sms_sent = Column(Integer, default=0)
    api_requests = Column(Integer, default=0)
    
    # Financeiro
    amount = Column(Numeric(10, 2), default=0)
    payment_status = Column(String(20), default="pending")  # pending, paid, overdue, grace
    paid_at = Column(DateTime)
    
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
```

### 2.4 — GlobalAuditLog

```python
# admin/models/audit.py
class GlobalAuditLog(Base):
    __tablename__ = "audit_global"
    __table_args__ = {"schema": "platform"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    actor_id = Column(String(255), nullable=False)  # "admin:uuid" ou "support:uuid"
    action = Column(String(100), nullable=False)  # "tenant.created", "impersonation.started"
    resource_type = Column(String(100))  # "tenant", "plan", "module"
    resource_id = Column(String(255))
    target_tenant_id = Column(String(100))
    details = Column(JSON, default={})
    ip_address = Column(String(45))
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
```

---

## 3. Serviços

### 3.1 — ProvisioningService

```python
# admin/services/provisioning_service.py

class ProvisioningService:
    """Orquestra o provisionamento completo de um novo tenant."""
    
    async def provision(self, tenant: Tenant) -> ProvisioningResult:
        """
        Passos (transacional):
        1. Criar schema "tenant_{id}" no PostgreSQL
        2. Rodar migrations Alembic nesse schema
        3. Criar grupo "tenant_{id}" no Keycloak
        4. Criar mapper "tenant_id" no grupo
        5. Criar usuário admin no Keycloak (email_admin)
        6. Associar usuário ao grupo
        7. Inserir seed data no schema (roles, configs)
        8. Marcar tenant.provisioned = True
        
        Rollback em caso de falha em qualquer passo.
        """
```

### 3.2 — TenantService

```python
# admin/services/tenant_service.py

class TenantService:
    async def create(self, data: TenantCreate) -> Tenant:
        # Validar CNPJ, gerar slug, salvar, triggerar provisioning
    
    async def suspend(self, tenant_id: str, reason: str) -> Tenant:
        # Marcar suspended, logar auditoria
    
    async def activate(self, tenant_id: str) -> Tenant:
        # Verificar billing OK, reativar
    
    async def list_tenants(self, filters, page, size) -> PaginatedResult:
        # Paginação, filtros por status/plano
    
    async def update_modules(self, tenant_id: str, modules: list[ModuleUpdate]) -> list[TenantModule]:
        # Validar contra o plano, ativar/desativar
```

---

## 4. Autenticação e Autorização

### Roles de Plataforma (Keycloak)

| Role | Escopo |
|---|---|
| `platform_admin` | Acesso total ao admin |
| `platform_support` | Read tenants + impersonação |
| `platform_finance` | Billing + relatórios |

### Guards nos Endpoints

```python
from intellicare_auth import get_current_user, get_user_roles

async def require_platform_role(role: str):
    """Dependency que exige role de plataforma."""
    async def _guard(user = Depends(get_current_user)):
        roles = get_user_roles(user)
        if role not in roles:
            raise HTTPException(403, f"Role '{role}' necessária")
        return user
    return _guard
```

---

## 5. Configuração

```python
# admin/config.py
class AdminConfig(BaseModuleConfig):
    module_name: str = "intellicare-admin"
    module_version: str = "1.0.0"
    
    # Database (schema platform)
    platform_schema: str = "platform"
    
    # Keycloak Admin
    keycloak_admin_url: str = "https://keycloak.gsi.srv.br"
    keycloak_admin_realm: str = "master"
    keycloak_admin_username: str = ""
    keycloak_admin_password: str = ""
    keycloak_target_realm: str = "bemcuidar"
    
    # Provisioning
    migration_script_path: str = "./migrations"
    
    # Trial
    trial_duration_days: int = 30
    
    # Billing
    billing_grace_period_days: int = 15
```
