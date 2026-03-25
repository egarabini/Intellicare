---
tipo: tecnica
demanda: DEM-084
titulo: Patient Identity Integration
status: planejada
dev: DEV-2
sprint: 2026-05-16
criado: 2026-03-23
---

# DEM-084 — Técnica: Patient Identity Integration

## 1. Migration tenant — `022_paciente_pessoa_id.sql`

```sql
-- db/tenant_migrations/022_paciente_pessoa_id.sql
ALTER TABLE {schema}.paciente
ADD COLUMN IF NOT EXISTS pessoa_id UUID;

-- Índice para lookup por pessoa_id (futuro: busca cross-tenant)
CREATE INDEX IF NOT EXISTS idx_paciente_pessoa_id
    ON {schema}.paciente(pessoa_id)
    WHERE pessoa_id IS NOT NULL;
```

Aplicar em staging:
```bash
sed 's/{schema}/demo/g' db/tenant_migrations/022_paciente_pessoa_id.sql | \
  docker compose exec -T db psql -U postgres -d intellicare
```

**Nota:** FK deliberadamente ausente — ver ADR-004. O `pessoa_id` é uma referência lógica.

---

## 2. `cuidado/services.py` — adaptar `create_patient()`

```python
from modules.identity.services import find_or_create_by_cpf
from modules.identity.repository import register_tenant_link

async def create_patient(
    ctx,
    db: AsyncSession,           # tenant session
    platform_db: AsyncSession,  # platform session
    payload: PatientCreateIn,
) -> PatientOut:

    pessoa_id = None

    # Integração com identity service (somente se CPF fornecido)
    if payload.cpf:
        cpf_clean = re.sub(r'\D', '', payload.cpf)
        pessoa = await find_or_create_by_cpf(
            platform_db,
            cpf=cpf_clean,
            nome_completo=payload.nome_completo,
            data_nascimento=payload.data_nascimento,
        )
        pessoa_id = pessoa.id

        # Registrar vínculo LGPD: esta pessoa está neste tenant
        await register_tenant_link(platform_db, pessoa_id, ctx.tenant_slug)

    async with tenant_session(ctx) as session:
        paciente = Paciente(
            **payload.model_dump(exclude={"cpf"}),
            pessoa_id=pessoa_id,
        )
        session.add(paciente)
        await session.commit()
        await session.refresh(paciente)
        return PatientOut.model_validate(paciente)
```

**Importante:** `create_patient()` agora recebe dois parâmetros de sessão. Atualizar todos os call sites.

---

## 3. `identity/repository.py` — `register_tenant_link()`

```python
async def register_tenant_link(
    db: AsyncSession,
    pessoa_id: uuid.UUID,
    tenant_slug: str,
) -> None:
    """
    Upsert: se o vínculo já existe (mesmo pessoa_id + tenant_slug),
    apenas reativa (ativo=True). Não duplica.
    """
    stmt = pg_insert(PessoaEstabelecimento).values(
        pessoa_id=pessoa_id,
        tenant_slug=tenant_slug,
        ativo=True,
    ).on_conflict_do_update(
        index_elements=["pessoa_id", "tenant_slug"],
        set_={"ativo": True, "data_desvinculo": None}
    )
    await db.execute(stmt)
    await db.commit()
```

---

## 4. `cuidado/routes.py` — injetar `platform_db`

```python
from packages.intellicare_core.database import get_platform_db

@router.post("/patients", response_model=PatientOut, status_code=201)
async def create_patient_endpoint(
    payload: PatientCreateIn,
    ctx: TenantContext = Depends(get_tenant_context),
    platform_db: AsyncSession = Depends(get_platform_db),
):
    return await create_patient(ctx, platform_db=platform_db, payload=payload)
```

---

## 5. `GET /cuidado/patients/{id}` — merge de dados

```python
async def get_patient(ctx, patient_id: uuid.UUID, platform_db: AsyncSession):
    async with tenant_session(ctx) as db:
        paciente = await db.get(Paciente, patient_id)
        if not paciente:
            raise HTTPException(404)

    # Enriquecer com dados canônicos se pessoa_id disponível
    if paciente.pessoa_id:
        pessoa = await get_pessoa_by_id(platform_db, paciente.pessoa_id)
        return PatientOut(
            **paciente.__dict__,
            nome_completo=pessoa.nome_completo,  # dado canônico sobrescreve local
            cpf=pessoa.cpf,
        )

    # Fallback legado — retornar dados do tenant
    return PatientOut.model_validate(paciente)
```

---

## 6. `GET /me/profile` (Portal do Paciente)

```python
@router.get("/me/profile", response_model=PatientProfileOut)
async def get_my_profile(
    ctx: TenantContext = Depends(get_tenant_context),
    platform_db: AsyncSession = Depends(get_platform_db),
    token_data: dict = Depends(get_current_patient_token),
):
    patient = await get_patient_by_keycloak_id(ctx, token_data["sub"])
    pessoa_id = patient.pessoa_id if patient else None

    if pessoa_id:
        pessoa = await get_pessoa_by_id(platform_db, pessoa_id)
        return PatientProfileOut(
            pessoa_id=str(pessoa_id),
            nome_completo=pessoa.nome_completo,
            cpf=pessoa.cpf,
            # dados operacionais continuam do tenant
            data_primeiro_atendimento=patient.data_primeiro_atendimento,
        )

    # Fallback legado
    return PatientProfileOut.model_validate(patient)
```

---

## 7. `PatientOut` schema — adicionar `pessoa_id`

```python
class PatientOut(BaseModel):
    id: uuid.UUID
    nome_completo: str
    cpf: Optional[str] = None
    pessoa_id: Optional[uuid.UUID] = None  # novo campo
    # ... campos existentes ...
```

---

## 8. Testes — `tests/test_patient_identity.py`

Cenários:
1. `POST /cuidado/patients` com CPF → `pessoa_id` preenchido no retorno
2. Mesmo CPF em dois tenants → mesmo `pessoa_id` (via mock platform_db)
3. `POST /cuidado/patients` sem CPF → `pessoa_id` null, sem erro
4. `GET /cuidado/patients/{id}` com `pessoa_id` → dados canônicos no response
5. `GET /cuidado/patients/{id}` sem `pessoa_id` (legado) → dados do tenant, sem erro
6. `GET /me/profile` com `pessoa_id` → retorna `pessoa_id` no response
7. Registro em `pessoa_estabelecimento` criado ao vincular

---

## Gotcha — dois AsyncSession no mesmo handler

`create_patient` agora usa `platform_db` (platform schema) e `tenant_session(ctx)` (tenant schema). São transações independentes — se o insert no tenant falhar após o `find_or_create` na plataforma, o registro em `platform.pessoa` persiste (isso é correto: a identidade existe, o vínculo de paciente ainda não). Não há two-phase commit — documentar no ADR-004.

---

## Gotcha — `PatientCreateIn` precisa de CPF

Verificar se `PatientCreateIn` já tem campo `cpf`. Se não tiver, adicionar como opcional:
```python
cpf: Optional[str] = None
```
Não breaking — campo opcional com default None.
