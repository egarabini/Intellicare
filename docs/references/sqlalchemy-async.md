---
tipo: referencia
tecnologia: SQLAlchemy Async
versao: "2.0+"
tags: [referencia, sqlalchemy, async, postgres, multi-tenancy]
---

# SQLAlchemy Async — Referência Rápida

> Padrões de acesso a dados usados no IntelliCare V3. Foco em async + multi-tenancy.

---

## Engine e Session Factory

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

engine = create_async_engine(
    "postgresql+asyncpg://user:pass@localhost:5432/intellicare",
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
)

AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)
```

---

## Tenant-Aware Session (schema por tenant)

```python
from sqlalchemy import text

async def tenant_session(ctx: TenantContext):
    """Cria session com search_path apontando para o schema do tenant."""
    async with AsyncSessionLocal() as session:
        schema = f"tenant_{ctx.slug}"
        await session.execute(text(f"SET search_path TO {schema}, public"))
        yield session
```

### Uso em endpoint

```python
@router.get("/patients")
async def list_patients(session = Depends(tenant_session)):
    result = await session.execute(select(Patient))
    return result.scalars().all()
```

---

## Declarative Models (ORM)

```python
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Integer, DateTime, func

class Base(DeclarativeBase):
    pass

class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(200))
    cpf: Mapped[str] = mapped_column(String(11), unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
```

---

## Queries Comuns

### Select com filtro

```python
from sqlalchemy import select

stmt = select(Patient).where(Patient.cpf == cpf)
result = await session.execute(stmt)
patient = result.scalar_one_or_none()
```

### Insert

```python
patient = Patient(full_name="João", cpf="12345678901")
session.add(patient)
await session.commit()
await session.refresh(patient)
```

### Update

```python
stmt = update(Patient).where(Patient.id == pid).values(full_name="Novo Nome")
await session.execute(stmt)
await session.commit()
```

### Paginação

```python
stmt = select(Patient).offset(skip).limit(limit).order_by(Patient.id)
result = await session.execute(stmt)
```

---

## Raw SQL (quando necessário)

```python
from sqlalchemy import text

result = await session.execute(
    text("SELECT * FROM :schema.patients WHERE cpf = :cpf"),
    {"schema": f"tenant_{slug}", "cpf": cpf}
)
rows = result.mappings().all()
```

---

## Schema Management (provisionamento)

```python
async def create_tenant_schema(slug: str):
    schema = f"tenant_{slug}"
    async with engine.begin() as conn:
        await conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
        await conn.execute(text(f"SET search_path TO {schema}"))
        # Rodar migrations ou CREATE TABLE
```

---

## Alembic (migrations async)

```ini
# alembic.ini
sqlalchemy.url = postgresql+asyncpg://...

[alembic]
script_location = migrations
```

```python
# env.py
from sqlalchemy.ext.asyncio import create_async_engine

async def run_migrations():
    engine = create_async_engine(url)
    async with engine.begin() as conn:
        await conn.run_sync(do_run_migrations)
```

---

## Links úteis

- [SQLAlchemy 2.0 Async](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [Mapped columns](https://docs.sqlalchemy.org/en/20/orm/mapped_attributes.html)
- [AsyncSession](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html#sqlalchemy.ext.asyncio.AsyncSession)
- [Connection pooling](https://docs.sqlalchemy.org/en/20/core/pooling.html)

