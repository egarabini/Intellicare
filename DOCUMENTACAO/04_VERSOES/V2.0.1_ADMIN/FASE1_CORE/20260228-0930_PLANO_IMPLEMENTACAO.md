# Fase 1 - Plano de Implementação: Módulo Admin - Core

> **DEV Atribuído:** A definir
> **Depende de:** Fase 0 (TenantContext + Infra)
> **Bloqueia:** Fase 2, Fase 3
> **Estimativa:** 12 dias

---

## Ordem de Execução

| # | Task | Estimativa | Depende de | Responsável |
|---|------|-----------|------------|-------------|
| 1 | Scaffold do módulo | 0.5 dia | Fase 0 completa | DEV |
| 2 | Schema + Migrations (platform) | 1 dia | Task 1 | DEV |
| 3 | Modelos ORM + Pydantic | 1 dia | Task 2 | DEV |
| 4 | TenantService (CRUD) | 2 dias | Task 3 | DEV |
| 5 | ProvisioningService (DB) | 1 dia | Task 3 | DEV |
| 6 | ProvisioningService (Keycloak) | 1.5 dias | Task 5 | DEV |
| 7 | Background Tasks + Retry | 1 dia | Task 6 | DEV |
| 8 | API Routes (tenants) | 1 dia | Tasks 4, 7 | DEV |
| 9 | Testes Integração | 1.5 dias | Task 8 | DEV |
| 10 | Testes E2E + Documentação | 1 dia | Task 9 | DEV |
| 11 | Seed Data (plans) | 0.5 dia | Task 2 | DEV |

**Total: 12 dias**

---

## Detalhamento das Tasks

### Task 1: Scaffold do Módulo (0.5 dia)

**Objetivo:** Criar estrutura base do módulo `intellicare-admin`

**Arquivos a criar:**

```
intellicare-admin/
├── admin/
│   ├── __init__.py
│   ├── config.py                 # AdminConfig
│   ├── models/
│   │   ├── __init__.py
│   │   ├── tenant.py
│   │   ├── plan.py
│   │   └── audit.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── tenant.py             # Pydantic models
│   │   └── common.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── tenant_service.py
│   │   ├── provisioning_service.py
│   │   └── keycloak_service.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── dependencies.py
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   └── tenants.py
│   │   └── app.py                # FastAPI app
│   ├── tasks/
│   │   ├── __init__.py
│   │   └── provisioning_tasks.py # Background tasks
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   ├── test_tenant_service.py
│   │   ├── test_provisioning.py
│   │   └── test_api.py
│   ├── migrations/
│   │   └── README.md
│   ├── pyproject.toml
│   ├── requirements.txt
│   ├── Dockerfile
│   └── README.md
```

**pyproject.toml:**

```toml
[project]
name = "intellicare-admin"
version = "2.0.1"
description = "Módulo de administração multi-tenant IntelliCare"
requires-python = ">=3.11"
dependencies = [
    "intellicare-core",
    "intellicare-auth",
    "fastapi>=0.109.0",
    "uvicorn[standard]>=0.27.0",
    "sqlalchemy>=2.0.25",
    "alembic>=1.13.0",
    "psycopg2-binary>=2.9.9",
    "pydantic>=2.5.0",
    "pydantic-settings>=2.1.0",
    "python-keycloak>=4.0.0",
    "celery>=5.3.0",
    "redis>=5.0.0",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]

[tool.coverage.run]
source = ["admin"]
omit = ["tests/*"]
```

**Dockerfile:**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Instalar dependências
COPY pyproject.toml requirements.txt ./
RUN pip install --no-cache-dir -e .

# Copiar código
COPY . .

# Expor porta
EXPOSE 8010

# Command
CMD ["uvicorn", "admin.api.app:app", "--host", "0.0.0.0", "--port", "8010"]
```

**Checklist:**
- [ ] Estrutura de diretórios criada
- [ ] pyproject.toml configurado
- [ ] Dockerfile criado
- [ ] README com instruções de execução

---

### Task 2: Schema + Migrations (1 dia)

**Objetivo:** Criar schema `platform` e migrations iniciais

**Migration 1: Criar schema platform**

```sql
-- migrations/versions/001_create_platform_schema.py

def upgrade():
    # Criar schema platform
    op.execute("CREATE SCHEMA IF NOT EXISTS platform")

    # Tabela tenants
    op.create_table(
        'tenants',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('tenant_id', sa.String(100), unique=True, nullable=False),
        sa.Column('nome_fantasia', sa.String(150), nullable=False),
        sa.Column('razao_social', sa.String(200), nullable=False),
        sa.Column('cnpj', sa.String(14), unique=True, nullable=False),
        sa.Column('email_admin', sa.String(255), unique=True, nullable=False),
        sa.Column('telefone', sa.String(15), nullable=False),
        sa.Column('logo_url', sa.String(255), nullable=True),
        sa.Column('cor_primaria', sa.String(7), default='#6366f1'),
        sa.Column('cor_secundaria', sa.String(7), default='#8b5cf6'),
        sa.Column('dominio_custom', sa.String(100), unique=True, nullable=True),
        sa.Column('endereco', sa.JSON(), nullable=True),
        sa.Column('plano_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(20), default='trial'),
        sa.Column('configuracoes', sa.JSON(), default={}),
        sa.Column('provisionado', sa.Boolean(), default=False),
        sa.Column('provisionado_em', sa.DateTime(), nullable=True),
        sa.Column('provisionamento_erro', sa.Text(), nullable=True),
        sa.Column('trial_expira_em', sa.DateTime(), nullable=True),
        sa.Column('suspendido_em', sa.DateTime(), nullable=True),
        sa.Column('suspendido_motivo', sa.Text(), nullable=True),
        sa.Column('criado_em', sa.DateTime(), default=sa.func.now()),
        sa.Column('atualizado_em', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['plano_id'], ['platform.plans.id']),
        schema='platform'
    )

    # Tabela plans
    op.create_table(
        'plans',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('nome', sa.String(50), unique=True, nullable=False),
        sa.Column('display_name', sa.String(100), nullable=False),
        sa.Column('max_usuarios', sa.Integer(), nullable=False),
        sa.Column('max_sms_mes', sa.Integer(), nullable=False),
        sa.Column('preco_mensal', sa.Numeric(10, 2), nullable=False),
        sa.Column('modulos_incluidos', sa.JSON(), nullable=False),
        sa.Column('criado_em', sa.DateTime(), default=sa.func.now()),
        schema='platform'
    )

    # Tabela tenant_modules
    op.create_table(
        'tenant_modules',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('modulo', sa.String(50), nullable=False),
        sa.Column('ativo', sa.Boolean(), default=True),
        sa.Column('configuracoes', sa.JSON(), default={}),
        sa.Column('criado_em', sa.DateTime(), default=sa.func.now()),
        sa.ForeignKeyConstraint(['tenant_id'], ['platform.tenants.id']),
        sa.UniqueConstraint('tenant_id', 'modulo', name='uq_tenant_module'),
        schema='platform'
    )

    # Tabela audit_global
    op.create_table(
        'audit_global',
        sa.Column('id', sa.BigInteger(), primary_key=True),
        sa.Column('tenant_id', sa.Integer(), nullable=True),
        sa.Column('acao', sa.String(50), nullable=False),
        sa.Column('actor', sa.String(100), nullable=False),
        sa.Column('detalhes', sa.JSON(), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(255), nullable=True),
        sa.Column('criado_em', sa.DateTime(), default=sa.func.now()),
        sa.Index('idx_audit_tenant', 'tenant_id'),
        sa.Index('idx_audit_criado_em', 'criado_em'),
        schema='platform'
    )

    # Índices
    op.create_index('idx_tenants_status', 'tenants', ['status'], schema='platform')
    op.create_index('idx_tenants_plano', 'tenants', ['plano_id'], schema='platform')

def downgrade():
    op.execute("DROP SCHEMA platform CASCADE")
```

**Migration 2: Seed plans**

```sql
-- migrations/versions/002_seed_default_plans.py

def upgrade():
    op.execute("""
        INSERT INTO platform.plans (nome, display_name, max_usuarios, max_sms_mes, preco_mensal, modulos_incluidos)
        VALUES
          ('trial',         'Trial (30 dias)',           5,    100,   0.00,    '["zilda","florence"]'),
          ('basico',        'Básico',                    20,   500,   497.00, '["zilda","florence","oswaldo","geralda"]'),
          ('profissional',  'Profissional',              100,  2000,  1497.00, '["zilda","florence","oswaldo","geralda","donabedian","comunicacao","grahame"]'),
          ('enterprise',    'Enterprise',                9999, 10000, 2997.00, '["zilda","florence","oswaldo","geralda","donabedian","comunicacao","grahame","wanda"]')
        ON CONFLICT (nome) DO NOTHING
    """)

def downgrade():
    op.execute("DELETE FROM platform.plans WHERE nome IN ('trial', 'basico', 'profissional', 'enterprise')")
```

**Checklist:**
- [ ] Schema `platform` criado
- [ ] Todas as tabelas criadas
- [ ] Foreign keys funcionando
- [ ] Índices criados
- [ ] Plans seed inseridos
- [ ] Migration reversível (downgrade)

---

### Task 3: Modelos ORM + Pydantic (1 dia)

**admin/models/tenant.py:**

```python
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from intellicare_core.database import Base

class Tenant(Base):
    __tablename__ = 'tenants'
    __table_args__ = {'schema': 'platform'}

    id = Column(Integer, primary_key=True)
    tenant_id = Column(String(100), unique=True, nullable=False, index=True)
    nome_fantasia = Column(String(150), nullable=False)
    razao_social = Column(String(200), nullable=False)
    cnpj = Column(String(14), unique=True, nullable=False)
    email_admin = Column(String(255), unique=True, nullable=False)
    telefone = Column(String(15), nullable=False)
    logo_url = Column(String(255), nullable=True)
    cor_primaria = Column(String(7), default='#6366f1')
    cor_secundaria = Column(String(7), default='#8b5cf6')
    dominio_custom = Column(String(100), unique=True, nullable=True)
    endereco = Column(JSON, nullable=True)
    plano_id = Column(Integer, ForeignKey('platform.plans.id'), nullable=False)
    status = Column(String(20), default='trial')
    configuracoes = Column(JSON, default=dict)
    provisionado = Column(Boolean, default=False)
    provisionado_em = Column(DateTime, nullable=True)
    provisionamento_erro = Column(Text, nullable=True)
    trial_expira_em = Column(DateTime, nullable=True)
    suspendido_em = Column(DateTime, nullable=True)
    suspenso_motivo = Column(Text, nullable=True)
    criado_em = Column(DateTime, default=func.now())
    atualizado_em = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    plano = relationship("Plan", back_populates="tenants")
    modules = relationship("TenantModule", back_populates="tenant", cascade="all, delete-orphan")
    audit_logs = relationship("GlobalAuditLog", back_populates="tenant")
```

**admin/schemas/tenant.py:**

```python
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import datetime

class TenantCreate(BaseModel):
    nome_fantasia: str = Field(..., min_length=3, max_length=150)
    razao_social: str = Field(..., min_length=3, max_length=200)
    cnpj: str = Field(..., pattern=r'^\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}$')
    email_admin: EmailStr
    telefone: str = Field(..., min_length=10, max_length=15)
    logo_url: Optional[str] = None
    cor_primaria: str = Field(default='#6366f1', pattern=r'^#[0-9A-Fa-f]{6}$')
    cor_secundaria: str = Field(default='#8b5cf6', pattern=r'^#[0-9A-Fa-f]{6}$')
    dominio_custom: Optional[str] = None
    endereco: Optional[dict] = None
    plano_id: int
    configuracoes: Optional[dict] = None

    @validator('cnpj')
    def validate_cnpj(cls, v):
        # Remove caracteres não numéricos
        numbers = ''.join(c for c in v if c.isdigit())
        if len(numbers) != 14:
            raise ValueError('CNPJ deve ter 14 dígitos')
        # TODO: Validar dígitos verificadores
        return v

class TenantResponse(BaseModel):
    id: int
    tenant_id: str
    nome_fantasia: str
    razao_social: str
    cnpj: str
    email_admin: str
    telefone: str
    logo_url: Optional[str]
    cor_primaria: str
    cor_secundaria: str
    dominio_custom: Optional[str]
    plano: 'PlanResponse'
    modulos_ativos: List[str]
    status: str
    provisionado: bool
    provisionado_em: Optional[datetime]
    trial_expira_em: Optional[datetime]
    criado_em: datetime
    atualizado_em: datetime

    class Config:
        from_attributes = True

class TenantUpdate(BaseModel):
    nome_fantasia: Optional[str] = Field(None, min_length=3, max_length=150)
    razao_social: Optional[str] = None
    email_admin: Optional[EmailStr] = None
    telefone: Optional[str] = None
    logo_url: Optional[str] = None
    cor_primaria: Optional[str] = None
    cor_secundaria: Optional[str] = None
    dominio_custom: Optional[str] = None
    endereco: Optional[dict] = None
    configuracoes: Optional[dict] = None
```

**Checklist:**
- [ ] Models ORM criados (Tenant, Plan, TenantModule, Audit)
- [ ] Pydantic schemas criados (Create, Update, Response)
- [ ] Validações funcionando (CNPJ, email, cores hex)
- [ ] Relationships configuradas

---

### Task 4: TenantService (CRUD) (2 dias)

**admin/services/tenant_service.py:**

```python
from typing import List, Optional
from sqlalchemy.orm import Session
from admin.models import Tenant, Plan, TenantModule
from admin.schemas import TenantCreate, TenantUpdate
from intellicare_core.exceptions import NotFoundError, ConflictError
import re

class TenantService:
    def __init__(self, db: Session):
        self.db = db

    async def create(self, data: TenantCreate) -> Tenant:
        # 1. Validar CNPJ único
        if self.db.query(Tenant).filter(Tenant.cnpj == data.cnpj).first():
            raise ConflictError("CNPJ já cadastrado")

        # 2. Validar email único
        if self.db.query(Tenant).filter(Tenant.email_admin == data.email_admin).first():
            raise ConflictError("Email já cadastrado")

        # 3. Validar plano existe
        plan = self.db.query(Plan).filter(Plan.id == data.plano_id).first()
        if not plan:
            raise NotFoundError("Plano não encontrado")

        # 4. Gerar tenant_id
        tenant_id = self._generate_tenant_id(data.nome_fantasia)

        # 5. Criar tenant
        tenant = Tenant(
            tenant_id=tenant_id,
            **data.dict(),
            status='trial',
            provisionado=False
        )

        self.db.add(tenant)
        self.db.commit()
        self.db.refresh(tenant)

        # 6. Ativar módulos do plano
        self._activate_plan_modules(tenant, plan)

        # 7. Agendar job de provisionamento
        from admin.tasks.provisioning_tasks import provision_tenant
        provision_tenant.delay(tenant.id)

        return tenant

    def _generate_tenant_id(self, nome: str) -> str:
        # Gerar slug
        slug = nome.lower()
        slug = re.sub(r'[^a-z0-9]+', '-', slug)
        slug = slug.strip('-')

        # Verificar duplicidade
        counter = 0
        base_slug = slug
        while self.db.query(Tenant).filter(Tenant.tenant_id == slug).first():
            counter += 1
            slug = f"{base_slug}-{counter}"

        return slug

    def _activate_plan_modules(self, tenant: Tenant, plan: Plan):
        for modulo in plan.modulos_incluidos:
            tm = TenantModule(
                tenant_id=tenant.id,
                modulo=modulo,
                ativo=True
            )
            self.db.add(tm)
        self.db.commit()

    def list(self, page: int = 1, per_page: int = 20,
             status: Optional[str] = None,
             plano_id: Optional[int] = None,
             search: Optional[str] = None) -> tuple[List[Tenant], int]:
        query = self.db.query(Tenant)

        # Filtros
        if status:
            query = query.filter(Tenant.status == status)
        if plano_id:
            query = query.filter(Tenant.plano_id == plano_id)
        if search:
            query = query.filter(
                (Tenant.nome_fantasia.ilike(f'%{search}%')) |
                (Tenant.cnpj.ilike(f'%{search}%')) |
                (Tenant.email_admin.ilike(f'%{search}%'))
            )

        # Contar total
        total = query.count()

        # Paginação
        offset = (page - 1) * per_page
        tenants = query.offset(offset).limit(per_page).all()

        return tenants, total

    def get(self, tenant_id: int) -> Tenant:
        tenant = self.db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if not tenant:
            raise NotFoundError("Tenant não encontrado")
        return tenant

    def update(self, tenant_id: int, data: TenantUpdate) -> Tenant:
        tenant = self.get(tenant_id)

        # Campos não editáveis após provisionamento
        if tenant.provisionado:
            non_editable = ['cnpj']
            for field in non_editable:
                if getattr(data, field) is not None:
                    raise ValueError(f"Campo {field} não pode ser alterado após provisionamento")

        # Atualizar campos
        for field, value in data.dict(exclude_unset=True).items():
            setattr(tenant, field, value)

        self.db.commit()
        self.db.refresh(tenant)
        return tenant

    def suspend(self, tenant_id: int, motivo: str, actor: str):
        tenant = self.get(tenant_id)
        tenant.status = 'suspended'
        tenant.suspendido_em = func.now()
        tenant.suspenso_motivo = motivo
        self.db.commit()

        # Registrar audit
        self._audit_log(tenant.id, 'suspend', actor, {'motivo': motivo})

    def activate(self, tenant_id: int, novo_plano_id: Optional[int], actor: str):
        tenant = self.get(tenant_id)

        if novo_plano_id and novo_plano_id < tenant.plano_id:
            raise ValueError("Não é permitido fazer downgrade de plano")

        tenant.status = 'active'
        tenant.suspendido_em = None
        tenant.suspenso_motivo = None

        if novo_plano_id:
            tenant.plano_id = novo_plano_id

        self.db.commit()

        # Registrar audit
        self._audit_log(tenant.id, 'activate', actor, {'novo_plano': novo_plano_id})

    def _audit_log(self, tenant_id: int, acao: str, actor: str, detalhes: dict):
        from admin.models import GlobalAuditLog
        log = GlobalAuditLog(
            tenant_id=tenant_id,
            acao=acao,
            actor=actor,
            detalhes=detalhes
        )
        self.db.add(log)
        self.db.commit()
```

**Checklist:**
- [ ] CRUD completo implementado
- [ ] Validações funcionando
- [ ] Paginação funcionando
- [ ] Filtros funcionando
- [ ] Busca funcionando
- [ ] Auditoria registrando ações
- [ ] Tests unitários (>80% cobertura)

---

### Task 5: ProvisioningService (DB) (1 dia)

**admin/services/provisioning_service.py:**

```python
from sqlalchemy import text
from admin.models import Tenant
from intellicare_core.database import engine
import logging

logger = logging.getLogger(__name__)

class ProvisioningService:
    def __init__(self, db: Session):
        self.db = db

    async def provision_database(self, tenant: Tenant) -> bool:
        """Criar schema e rodar migrations"""
        try:
            schema_name = f"tenant_{tenant.tenant_id}"

            # 1. Criar schema
            logger.info(f"Criando schema {schema_name}")
            with engine.connect() as conn:
                conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}"))
                conn.commit()

            # 2. Rodar migrations no schema
            logger.info(f"Rodando migrations no schema {schema_name}")
            # TODO: Executar alembic upgrade no schema específico
            # subprocess.run(["alembic", "upgrade", "head", "-x", f"schema={schema_name}"])

            # 3. Seed data
            logger.info(f"Inserindo seed data no schema {schema_name}")
            self._insert_seed_data(tenant)

            return True

        except Exception as e:
            logger.error(f"Erro ao provisionar DB: {e}")
            # Rollback: deletar schema criado
            try:
                with engine.connect() as conn:
                    conn.execute(text(f"DROP SCHEMA IF EXISTS {schema_name} CASCADE"))
                    conn.commit()
            except:
                pass
            return False

    def _insert_seed_data(self, tenant: Tenant):
        """Inserir dados iniciais no schema do tenant"""
        schema_name = f"tenant_{tenant.tenant_id}"

        with engine.connect() as conn:
            # Roles padrão
            conn.execute(text(f"""
                INSERT INTO {schema_name}.roles (nome, permissoes)
                VALUES
                  ('ADMIN', '["*"]'),
                  ('PROFISSIONAL', '["zilda.read", "oswaldo.read"]'),
                  ('VIEW_ONLY', '["*.read"]')
                ON CONFLICT DO NOTHING
            """))

            # Configurações padrão
            conn.execute(text(f"""
                INSERT INTO {schema_name}.configuracoes (chave, valor)
                VALUES
                  ('timezone', 'America/Sao_Paulo'),
                  ('idioma', 'pt-BR'),
                  ('formato_data', 'DD/MM/YYYY')
                ON CONFLICT (chave) DO NOTHING
            """))

            conn.commit()
```

**Checklist:**
- [ ] Schema criado com sucesso
- [ ] Migrations rodadas no schema
- [ ] Seed data inserida
- [ ] Rollback funcionando em caso de erro

---

### Task 6: ProvisioningService (Keycloak) (1.5 dias)

**admin/services/keycloak_service.py:**

```python
from python_keycloak import KeycloakAdmin
from admin.config import settings

class KeycloakService:
    def __init__(self):
        self.kc = KeycloakAdmin(
            server_url=settings.keycloak_url,
            username=settings.keycloak_user,
            password=settings.keycloak_password,
            realm_name=settings.keycloak_realm,
            verify=True
        )

    async def create_tenant_group(self, tenant_id: str) -> str:
        """Criar grupo no Keycloak para o tenant"""
        group_name = f"tenant_{tenant_id}"

        try:
            group = self.kc.create_group(
                payload={
                    "name": group_name,
                    "attributes": {
                        "tenant_id": [tenant_id]
                    }
                }
            )
            group_id = group.get("id")

            # Criar mapper para tenant_id
            self._create_tenant_mapper(group_id)

            return group_id

        except Exception as e:
            logger.error(f"Erro ao criar grupo KC: {e}")
            raise

    def _create_tenant_mapper(self, group_id: str):
        """Criar protocol mapper para tenant_id no grupo"""
        mapper_payload = {
            "name": "tenant_id",
            "protocol": "openid-connect",
            "protocolMapper": "oidc-usermodel-attribute-mapper",
            "consentRequired": False,
            "claimName": "tenant_id",
            "userAttribute": "tenant_id"
        }

        self.kc.create_group_mapper(group_id, mapper_payload)

    async def create_admin_user(self, tenant: Tenant, temp_password: str) -> str:
        """Criar usuário admin-local no Keycloak"""
        try:
            user_payload = {
                "username": f"admin_{tenant.tenant_id}",
                "email": tenant.email_admin,
                "enabled": True,
                "emailVerified": False,
                "attributes": {
                    "tenant_id": [tenant.tenant_id],
                    "role": ["ADMIN"],
                    "nome": [tenant.nome_fantasia]
                },
                "credentials": [
                    {
                        "type": "password",
                        "value": temp_password,
                        "temporary": True
                    }
                ]
            }

            user_id = self.kc.create_user(user_payload)

            # Adicionar ao grupo do tenant
            group_id = self.kc.get_group_by_name(f"tenant_{tenant.tenant_id}")
            self.kc.group_user_add(user_id, group_id["id"])

            # Enviar email de reset de senha
            self.kc.send_update_account(
                user_id=user_id,
                payload=["UPDATE_PASSWORD"]
            )

            return user_id

        except Exception as e:
            logger.error(f"Erro ao criar usuário KC: {e}")
            raise
```

**Checklist:**
- [ ] Conexão com Keycloak Admin API funcionando
- [ ] Grupo criado com tenant_id attribute
- [ ] Protocol mapper criado
- [ ] Usuário admin criado
- [ ] Email de reset de senha enviado
- [ ] Rollback funcionando (deletar grupo/usuário em caso de erro)

---

### Task 7: Background Tasks + Retry (1 dia)

**admin/tasks/provisioning_tasks.py:**

```python
from celery import Celery
from admin.services.provisioning_service import ProvisioningService
from admin.services.keycloak_service import KeycloakService
from admin.models import Tenant
from intellicare_core.database import SessionLocal
import logging

celery_app = Celery('admin')
logger = logging.getLogger(__name__)

@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,)
)
def provision_tenant(self, tenant_id: int):
    """Background task para provisionar tenant"""
    db = SessionLocal()
    try:
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if not tenant:
            logger.error(f"Tenant {tenant_id} não encontrado")
            return

        tenant.status = 'provisioning'
        db.commit()

        # 1. Provisionar DB
        prov_db = ProvisioningService(db)
        if not await prov_db.provision_database(tenant):
            raise Exception("Falha ao provisionar database")

        # 2. Provisionar Keycloak
        kc_service = KeycloakService()
        try:
            group_id = await kc_service.create_tenant_group(tenant.tenant_id)
            user_id = await kc_service.create_admin_user(tenant)
        except Exception as e:
            # Rollback: deletar schema DB
            await prov_db.rollback_database(tenant)
            raise Exception(f"Falha ao provisionar Keycloak: {e}")

        # 3. Sucesso
        tenant.provisionado = True
        tenant.provisionado_em = func.now()
        tenant.status = 'trial'
        db.commit()

        logger.info(f"Tenant {tenant.tenant_id} provisionado com sucesso")

    except Exception as e:
        logger.error(f"Erro ao provisionar tenant {tenant_id}: {e}")
        tenant.provisionado = False
        tenant.provisionamento_erro = str(e)
        db.commit()

        # Re-raise para retry
        raise

    finally:
        db.close()
```

**Checklist:**
- [ ] Celery configurado
- [ ] Worker rodando
- [ ] Task sendo chamada ao criar tenant
- [ ] Retry automático funcionando
- [ ] Logs detalhados

---

### Task 8: API Routes (1 dia)

**admin/api/routes/tenants.py:**

```python
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from admin.api.dependencies import get_db, get_current_user
from admin.schemas import TenantCreate, TenantUpdate, TenantResponse
from admin.services.tenant_service import TenantService
from typing import List, Optional

router = APIRouter(prefix="/admin/tenants", tags=["Tenants"])

@router.post("/", response_model=TenantResponse, status_code=201)
async def create_tenant(
    data: TenantCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    service = TenantService(db)
    tenant = await service.create(data)
    return tenant

@router.get("/", response_model=List[TenantResponse])
async def list_tenants(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    plano_id: Optional[int] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    service = TenantService(db)
    tenants, total = service.list(page, per_page, status, plano_id, search)
    return tenants

@router.get("/{tenant_id}", response_model=TenantResponse)
async def get_tenant(
    tenant_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    service = TenantService(db)
    tenant = service.get(tenant_id)
    return tenant

@router.patch("/{tenant_id}", response_model=TenantResponse)
async def update_tenant(
    tenant_id: int,
    data: TenantUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    service = TenantService(db)
    tenant = service.update(tenant_id, data)
    return tenant

@router.post("/{tenant_id}/suspend")
async def suspend_tenant(
    tenant_id: int,
    motivo: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    service = TenantService(db)
    service.suspend(tenant_id, motivo, current_user.username)
    return {"message": "Tenant suspenso"}

@router.post("/{tenant_id}/activate")
async def activate_tenant(
    tenant_id: int,
    novo_plano_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    service = TenantService(db)
    service.activate(tenant_id, novo_plano_id, current_user.username)
    return {"message": "Tenant reativado"}
```

**Checklist:**
- [ ] Todas as rotas implementadas
- [ ] Validações funcionando
- [ ] Documentação OpenAPI gerada
- [ ] Autenticação JWT funcionando
- [ ] Autorização (PLATFORM_ADMIN) funcionando

---

### Task 9-11: Testes e Documentação (3.5 dias)

**Omitido por brevidade, mas inclui:**
- Testes unitários (pytest)
- Testes de integração (com banco de teste)
- Testes E2E (com Keycloak mock)
- Documentação da API (OpenAPI)
- README com instruções de execução

---

## Checklist Final da Fase 1

### Código
- [ ] Módulo scaffolded e importável
- [ ] Schema `platform` criado
- [ ] Models + Schemas implementados
- [ ] TenantService completo (CRUD)
- [ ] ProvisioningService DB implementado
- [ ] ProvisioningService Keycloak implementado
- [ ] Background tasks funcionando
- [ ] API REST completa

### Qualidade
- [ ] Testes unitários ≥80% de cobertura
- [ ] Testes de integração passando
- [ ] Logs estruturados em JSON
- [ ] Validações de CNPJ funcionando
- [ ] Rollback automatizado em caso de erro

### Documentação
- [ ] README com instruções de execução
- [ ] OpenAPI documentation
- [ ] Exemplos de requests/responses
- [ ] Diagrama de sequência de provisionamento

---

## Próxima Fase

Após conclusão da **Fase 1**, iniciar **Fase 2** - Planos e Billing.
