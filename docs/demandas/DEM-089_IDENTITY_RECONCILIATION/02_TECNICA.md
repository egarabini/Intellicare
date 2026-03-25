# DEM-089 — Especificação Técnica

## Backend — Módulo Identity (extensão)

### Novos endpoints em `modules/identity/router.py`

```python
# POST /identity/admin/reconcile
# Requer role PLATFORM_ADMIN
# Query param: scope = "patients" | "professionals" | "all"

@router.post("/admin/reconcile")
async def reconcile_identities(
    scope: str = "patients",
    db: AsyncSession = Depends(get_tenant_db),        # tenant específico ou ALL
    platform_db: AsyncSession = Depends(get_platform_db),
    _=Depends(require_role("PLATFORM_ADMIN"))
):
    ...

# GET /identity/admin/stats
# Requer role PLATFORM_ADMIN
@router.get("/admin/stats")
async def identity_stats(
    platform_db: AsyncSession = Depends(get_platform_db),
    _=Depends(require_role("PLATFORM_ADMIN"))
):
    ...
```

### Lógica de reconciliação

```python
# modules/identity/services.py

async def reconcile_tenant_patients(db, platform_db, tenant_id):
    """
    Busca pacientes com cpf IS NOT NULL AND pessoa_id IS NULL.
    Para cada um, chama find_or_create_by_cpf() e UPDATE paciente.
    """
    rows = await db.execute(text("""
        SELECT id, cpf, nome
        FROM pacientes
        WHERE cpf IS NOT NULL AND pessoa_id IS NULL
    """))

    processed = 0
    linked = 0
    errors = []

    for row in rows.fetchall():
        try:
            cpf_digits = re.sub(r'\D', '', row.cpf)
            if not cpf_digits:
                continue
            record = await find_or_create_by_cpf(platform_db, cpf_digits, row.nome, tenant_id)
            await db.execute(text("""
                UPDATE pacientes SET pessoa_id = :pessoa_id WHERE id = :id
            """), {"pessoa_id": record["id"], "id": row.id})
            linked += 1
        except Exception as e:
            errors.append({"id": row.id, "error": str(e)})
        finally:
            processed += 1

    await db.commit()
    return {"processed": processed, "linked": linked, "skipped": 0, "errors": errors}
```

### Stats query (cross-tenant via platform schema)

```sql
-- GET /identity/admin/stats
SELECT
    pf.id,
    COUNT(DISTINCT pe.tenant_id) as tenant_count
FROM platform.pessoa_fisica pf
LEFT JOIN platform.pessoa_estabelecimento pe ON pe.pessoa_id = pf.id
GROUP BY pf.id;
```

**Nota:** Stats por tenant requerem acesso a cada schema de tenant para contar `pacientes.pessoa_id IS NOT NULL`. Implementar como query paralela em `asyncio.gather()` sobre os tenants ativos.

---

## Frontend — AdminUI

### Nova rota

```
/admin-ui/identity   →   IdentityPage.tsx
```

### Componente `IdentityPage.tsx`

```tsx
// Estrutura básica — Mantine v7
<Stack>
  <Title order={2}>Identidade Centralizada</Title>

  <SimpleGrid cols={3}>
    <StatCard label="Total pessoas" value={stats.total_pessoas} />
    <StatCard label="Pacientes vinculados" value={stats.patients_linked} />
    <StatCard label="Profissionais vinculados" value={stats.professionals_linked} />
  </SimpleGrid>

  <Table>
    {/* Por tenant: slug, pacientes com pessoa_id / total, cobertura % */}
  </Table>

  <Button onClick={openReconcileModal}>Reconciliar identidades</Button>

  <ConfirmModal onConfirm={() => runReconcile("all")} />
</Stack>
```

### NavLink no AdminUI

Adicionar "Identidade" ao nav lateral do AdminUI, junto com "Servidores", "Módulos" etc.

---

## Testes

```python
# test_identity_reconciliation.py

def test_reconcile_patients_links_existing_cpf():
    """Paciente pré-existente com CPF → reconcile → pessoa_id preenchido"""

def test_reconcile_idempotent():
    """Rodar reconcile 2x → segundo retorna linked=0, sem duplicatas"""

def test_reconcile_skip_null_cpf():
    """Pacientes sem CPF → skipped, não erram"""

def test_reconcile_error_isolation():
    """CPF inválido em 1 registro não aborta batch"""

def test_identity_stats_returns_coverage():
    """GET /identity/admin/stats → coverage % correto"""

def test_reconcile_requires_platform_admin():
    """Role TENANT_GESTOR → 403"""
```

Total esperado: 6 testes
