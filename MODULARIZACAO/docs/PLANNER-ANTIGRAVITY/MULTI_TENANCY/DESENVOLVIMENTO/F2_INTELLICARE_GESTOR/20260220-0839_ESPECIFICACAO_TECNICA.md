# F2 — Especificação Técnica: intellicare-gestor

> **Módulo:** `intellicare-gestor` (NOVO)  
> **Schema:** `tenant_{id}` | **Porta:** 8011  
> **Stack:** Python 3.11+, FastAPI, SQLAlchemy 2.x, Keycloak Admin API

---

## 1. Estrutura do Módulo

```
intellicare-gestor/
├── gestor/
│   ├── __init__.py
│   ├── config.py                  # GestorConfig
│   ├── models/
│   │   ├── user.py                # TenantUser ORM
│   │   ├── role.py                # Role, Permission, UserRole ORM
│   │   ├── sector.py              # Sector ORM
│   │   ├── settings.py            # TenantSetting ORM
│   │   └── audit.py               # LocalAuditLog ORM
│   ├── schemas/
│   │   ├── user_schemas.py        # Pydantic schemas
│   │   ├── role_schemas.py
│   │   └── sector_schemas.py
│   ├── services/
│   │   ├── user_service.py        # CRUD + KC sync
│   │   ├── role_service.py        # RBAC logic
│   │   ├── sector_service.py
│   │   ├── settings_service.py
│   │   └── audit_service.py
│   ├── api/
│   │   ├── app.py
│   │   ├── user_routes.py
│   │   ├── role_routes.py
│   │   ├── sector_routes.py
│   │   ├── settings_routes.py
│   │   ├── audit_routes.py
│   │   └── dashboard_routes.py
│   └── permissions.py             # Registry de permissões válidas
├── tests/
├── pyproject.toml
└── README.md
```

---

## 2. Modelos ORM

### 2.1 — TenantUser

```python
class TenantUser(Base):
    __tablename__ = "users"
    # Schema definido dinamicamente via TenantContext
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    keycloak_user_id = Column(String(255), unique=True)
    nome = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    cpf = Column(String(14), unique=True)
    cargo = Column(String(100))  # "Médico", "Enfermeiro", etc.
    conselho = Column(String(50))  # "CRM-SP 123456"
    sector_id = Column(UUID, ForeignKey("sectors.id"))
    active = Column(Boolean, default=True)
    invited_at = Column(DateTime)
    last_login_at = Column(DateTime)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
```

### 2.2 — Role + Permission

```python
class Role(Base):
    __tablename__ = "roles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, unique=True)
    display_name = Column(String(255))
    is_system = Column(Boolean, default=False)  # True = seed role, não pode deletar
    permissions = Column(JSON, default=[])  # ["oswaldo.classificar", "florence.ver"]
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))

class UserRole(Base):
    __tablename__ = "user_roles"
    
    user_id = Column(UUID, ForeignKey("users.id"), primary_key=True)
    role_id = Column(UUID, ForeignKey("roles.id"), primary_key=True)
    assigned_at = Column(DateTime, default=lambda: datetime.now(UTC))
    assigned_by = Column(UUID)  # Quem atribuiu
```

### 2.3 — Sector

```python
class Sector(Base):
    __tablename__ = "sectors"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    type = Column(String(50))  # "UTI", "Enfermaria", etc.
    parent_id = Column(UUID, ForeignKey("sectors.id"), nullable=True)  # Hierarquia
    responsavel_id = Column(UUID, ForeignKey("users.id"))
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
```

### 2.4 — TenantSetting

```python
class TenantSetting(Base):
    __tablename__ = "settings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    category = Column(String(100), nullable=False)  # "branding", "comunicacao", "modulos"
    key = Column(String(255), nullable=False, unique=True)
    value = Column(Text)
    value_type = Column(String(20), default="string")  # string, number, boolean, json
    updated_at = Column(DateTime, onupdate=lambda: datetime.now(UTC))
    updated_by = Column(UUID)
```

### 2.5 — LocalAuditLog

```python
class LocalAuditLog(Base):
    __tablename__ = "audit_local"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID, ForeignKey("users.id"))
    action = Column(String(100), nullable=False)  # "user.created", "role.updated"
    resource_type = Column(String(100))
    resource_id = Column(String(255))
    details = Column(JSON, default={})
    ip_address = Column(String(45))
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
```

---

## 3. Integração com TenantContext (F0)

Todos os endpoints usam `get_tenant_context()` de F0:

```python
from intellicare_auth import get_tenant_context
from intellicare_core.tenant import TenantContext, TenantAwareSessionFactory

@router.get("/gestor/users")
async def list_users(
    ctx: TenantContext = Depends(get_tenant_context),
    session_factory: TenantAwareSessionFactory = Depends(get_session_factory),
):
    session = await session_factory.get_session(ctx)
    # Queries vão automaticamente para tenant_{id}.users
    users = await session.execute(select(TenantUser).where(TenantUser.active == True))
    return users.scalars().all()
```

---

## 4. Permissões — Registry

```python
# gestor/permissions.py
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

def validate_permission(perm: str) -> bool:
    """Valida formato 'modulo.acao'."""
    parts = perm.split(".")
    if len(parts) != 2:
        return False
    module, action = parts
    return module in VALID_PERMISSIONS and action in VALID_PERMISSIONS[module]
```

---

## 5. Middleware de Verificação de Permissão

```python
# gestor/middleware.py
from functools import wraps

def require_permission(permission: str):
    """Decorator para exigir permissão específica."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, ctx: TenantContext, **kwargs):
            user_permissions = await get_user_permissions(ctx)
            if permission not in user_permissions and "*" not in user_permissions:
                raise HTTPException(403, f"Permissão '{permission}' necessária")
            return await func(*args, ctx=ctx, **kwargs)
        return wrapper
    return decorator
```

---

## 6. Seed Data (inserido pelo ProvisioningService de F1)

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

DEFAULT_SETTINGS = [
    {"category": "branding", "key": "nome_exibicao", "value": "", "value_type": "string"},
    {"category": "branding", "key": "fuso_horario", "value": "America/Sao_Paulo", "value_type": "string"},
    {"category": "comunicacao", "key": "sms_provider", "value": "twilio", "value_type": "string"},
    {"category": "comunicacao", "key": "email_smtp_host", "value": "", "value_type": "string"},
]
```
