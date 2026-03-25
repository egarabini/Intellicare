---
tipo: tecnica
demanda: DEM-083
titulo: ADR-004 + Identity Foundation
status: planejada
dev: CODEX
sprint: 2026-05-16
criado: 2026-03-23
---

# DEM-083 — Técnica: ADR-004 + Identity Foundation

## 1. ADR-004

Criar `docs/adr/ADR-004-identity-centralization.md` seguindo o padrão dos ADRs existentes (ADR-001 executor matrix, ADR-002 Marie).

Estrutura mínima:
```markdown
# ADR-004 — Centralização de Identidade em platform.pessoa

## Status: Aceito

## Contexto
[problema da duplicação cross-tenant]

## Decisão
platform.pessoa como SSOT. Tenant schemas mantêm dados operacionais com pessoa_id FK lógico.

## Alternativas consideradas
- Manter duplicação (descartado: LGPD inviável em escala)
- Schema `public` (descartado: conflito com namespace padrão PostgreSQL)
- Microserviço externo (descartado: complexidade prematura)

## Consequências
- Novos registros: find-or-create por CPF antes de criar paciente/profissional
- Dados existentes: migração gradual por reconciliação de CPF (sprint futura)
- FK é lógica (UUID), não físico-enforced entre schemas diferentes
```

---

## 2. Migration 021 — `db/platform_migrations/021_pessoa_identity.sql`

```sql
-- platform.pessoa — entidade base
CREATE TABLE IF NOT EXISTS platform.pessoa (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tipo        VARCHAR(10) NOT NULL CHECK (tipo IN ('FISICA', 'JURIDICA')),
    created_at  TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMP NOT NULL DEFAULT NOW()
);

-- platform.pessoa_fisica
CREATE TABLE IF NOT EXISTS platform.pessoa_fisica (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pessoa_id       UUID NOT NULL UNIQUE REFERENCES platform.pessoa(id) ON DELETE CASCADE,
    nome_completo   VARCHAR(255) NOT NULL,
    cpf             VARCHAR(11)  UNIQUE,
    data_nascimento DATE,
    genero          VARCHAR(20),
    updated_at      TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_pessoa_fisica_cpf
    ON platform.pessoa_fisica(cpf) WHERE cpf IS NOT NULL;

-- platform.pessoa_juridica
CREATE TABLE IF NOT EXISTS platform.pessoa_juridica (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pessoa_id    UUID NOT NULL UNIQUE REFERENCES platform.pessoa(id) ON DELETE CASCADE,
    razao_social VARCHAR(255) NOT NULL,
    nome_fantasia VARCHAR(255),
    cnpj         VARCHAR(14) UNIQUE,
    updated_at   TIMESTAMP NOT NULL DEFAULT NOW()
);

-- platform.pessoa_contato — telefones, e-mails e endereços unificados
CREATE TABLE IF NOT EXISTS platform.pessoa_contato (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pessoa_id     UUID NOT NULL REFERENCES platform.pessoa(id) ON DELETE CASCADE,
    tipo_contato  VARCHAR(20) NOT NULL CHECK (tipo_contato IN ('TELEFONE', 'EMAIL', 'ENDERECO')),
    valor         TEXT NOT NULL,
    subtipo       VARCHAR(50),   -- ex: 'CELULAR', 'RESIDENCIAL', 'COMERCIAL'
    principal     BOOLEAN NOT NULL DEFAULT FALSE,
    updated_at    TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE (pessoa_id, tipo_contato, valor)
);

-- platform.pessoa_estabelecimento — vínculo LGPD pessoa ↔ tenant
CREATE TABLE IF NOT EXISTS platform.pessoa_estabelecimento (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pessoa_id        UUID NOT NULL REFERENCES platform.pessoa(id) ON DELETE CASCADE,
    tenant_slug      VARCHAR(100) NOT NULL,
    data_vinculo     TIMESTAMP NOT NULL DEFAULT NOW(),
    data_desvinculo  TIMESTAMP,
    ativo            BOOLEAN NOT NULL DEFAULT TRUE,
    UNIQUE (pessoa_id, tenant_slug)
);

CREATE INDEX IF NOT EXISTS idx_pessoa_estabelecimento_tenant
    ON platform.pessoa_estabelecimento(tenant_slug) WHERE ativo = TRUE;
```

Aplicar com:
```bash
psql -U postgres -d intellicare -f db/platform_migrations/021_pessoa_identity.sql
```

---

## 3. Módulo `modules/identity/`

### Estrutura de arquivos

```
modules/identity/
├── __init__.py
├── models.py       # SQLAlchemy models — platform.pessoa*
├── schemas.py      # Pydantic schemas in/out
├── repository.py   # queries diretas no platform schema
├── services.py     # find_or_create_by_cpf()
└── router.py       # endpoints REST
```

### `models.py` — SQLAlchemy

```python
from sqlalchemy import Column, String, Boolean, Date, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
import uuid
from packages.intellicare_core.database import Base

class Pessoa(Base):
    __tablename__ = "pessoa"
    __table_args__ = {"schema": "platform"}

    id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tipo       = Column(String(10), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class PessoaFisica(Base):
    __tablename__ = "pessoa_fisica"
    __table_args__ = {"schema": "platform"}

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pessoa_id       = Column(UUID(as_uuid=True), ForeignKey("platform.pessoa.id"), unique=True, nullable=False)
    nome_completo   = Column(String(255), nullable=False)
    cpf             = Column(String(11), unique=True)
    data_nascimento = Column(Date)
    genero          = Column(String(20))
    updated_at      = Column(DateTime, server_default=func.now(), onupdate=func.now())
```

### `services.py` — find_or_create

```python
from sqlalchemy.ext.asyncio import AsyncSession
from .repository import get_pessoa_by_cpf, create_pessoa_fisica
from .schemas import PessoaFisicaIn, PessoaOut

async def find_or_create_by_cpf(
    db: AsyncSession,
    cpf: str,
    nome_completo: str,
    data_nascimento=None,
    genero: str = None,
) -> PessoaOut:
    """
    Idempotente: se CPF já existe, retorna o registro existente.
    Se não existe, cria platform.pessoa + platform.pessoa_fisica.
    """
    existing = await get_pessoa_by_cpf(db, cpf)
    if existing:
        return existing
    return await create_pessoa_fisica(db, PessoaFisicaIn(
        nome_completo=nome_completo,
        cpf=cpf,
        data_nascimento=data_nascimento,
        genero=genero,
    ))
```

### `router.py` — endpoints

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from packages.intellicare_core.database import get_platform_db
from .services import find_or_create_by_cpf
from .repository import get_pessoa_by_cpf, get_pessoa_by_id
from .schemas import PessoaFisicaIn, PessoaOut

router = APIRouter(prefix="/identity", tags=["identity"])

@router.get("/pessoas/cpf/{cpf}", response_model=PessoaOut)
async def lookup_by_cpf(cpf: str, db: AsyncSession = Depends(get_platform_db)):
    pessoa = await get_pessoa_by_cpf(db, cpf)
    if not pessoa:
        raise HTTPException(status_code=404, detail="Pessoa não encontrada")
    return pessoa

@router.post("/pessoas", response_model=PessoaOut, status_code=201)
async def create_or_get_pessoa(
    payload: PessoaFisicaIn,
    db: AsyncSession = Depends(get_platform_db)
):
    return await find_or_create_by_cpf(
        db, payload.cpf, payload.nome_completo,
        payload.data_nascimento, payload.genero
    )

@router.get("/pessoas/{pessoa_id}", response_model=PessoaOut)
async def get_pessoa(pessoa_id: str, db: AsyncSession = Depends(get_platform_db)):
    pessoa = await get_pessoa_by_id(db, pessoa_id)
    if not pessoa:
        raise HTTPException(status_code=404, detail="Pessoa não encontrada")
    return pessoa
```

### `schemas.py`

```python
from pydantic import BaseModel
from typing import Optional
from datetime import date
import uuid

class PessoaFisicaIn(BaseModel):
    nome_completo: str
    cpf: Optional[str] = None
    data_nascimento: Optional[date] = None
    genero: Optional[str] = None

class PessoaOut(BaseModel):
    id: uuid.UUID
    tipo: str
    nome_completo: str
    cpf: Optional[str]
    data_nascimento: Optional[date]

    class Config:
        from_attributes = True
```

---

## 4. Registro no router principal

Em `main.py` ou `modules/router.py`:
```python
from modules.identity.router import router as identity_router
app.include_router(identity_router)
```

---

## 5. Testes — `tests/test_identity_foundation.py`

Cenários obrigatórios:
1. `POST /identity/pessoas` com CPF novo → 201, retorna UUID
2. `POST /identity/pessoas` com mesmo CPF → 201, retorna **mesmo UUID** (idempotência)
3. `GET /identity/pessoas/cpf/{cpf}` CPF existente → 200
4. `GET /identity/pessoas/cpf/00000000000` CPF inexistente → 404
5. `GET /identity/pessoas/{id}` UUID existente → 200 com nome_completo
6. Migration 021 idempotente — rodar duas vezes sem erro (`IF NOT EXISTS`)

---

## Gotcha — `get_platform_db` vs `tenant_session`

O módulo `identity` acessa o schema `platform`, não um schema de tenant. Usar `get_platform_db` (que já existe para `prompt_templates`, `users`). **Não usar** `tenant_session(ctx)` aqui — identidade é cross-tenant por definição.

---

## Gotcha — CPF sem formatação

Armazenar CPF sempre sem formatação: `12345678901` (11 dígitos, sem pontos ou hífen). Normalizar no `services.py` antes de qualquer consulta ou insert:
```python
cpf_clean = re.sub(r'\D', '', cpf)
```

---

## Gotcha — FK lógica, não física entre schemas

A tabela `{schema}.paciente` vai ganhar `pessoa_id UUID` na DEM-084. Essa FK é **lógica** — não há `REFERENCES platform.pessoa(id)` na migration de tenant porque:
1. Se o tenant for migrado para banco separado, a FK física quebraria
2. A integridade é garantida pela aplicação (identity service sempre cria o registro antes)

Documentar isso no ADR-004.
