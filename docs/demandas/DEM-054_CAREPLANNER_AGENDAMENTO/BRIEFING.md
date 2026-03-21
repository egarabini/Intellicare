# DEM-054 — CarePlanner × Agendamento (Link Bidirecional)

> **Dev:** DEV-1
> **Estimativa:** ~3h
> **Dependência:** DEM-029 (agendamentos), DEM-047 a DEM-050 (CarePlanner multi-canal)

---

## Contexto

Hoje uma jornada CarePlanner e um agendamento clínico existem em silos. O gestor
precisa abrir o CarePlanner para disparar uma jornada e ir ao módulo de agendamentos
para ver a consulta vinculada. Esta DEM cria o elo entre os dois módulos:

- Ao disparar uma jornada, o gestor pode opcionalmente vincular a um `appointment_id`
- A timeline da jornada exibe o agendamento vinculado com link direto
- A tela de detalhe do agendamento exibe a jornada CarePlanner ativa (se houver)

---

## Fase A — Backend

### STEP-001 — Migration

`migrations/012_careplanner_appointment_link.sql`:

```sql
ALTER TABLE care_tasks
  ADD COLUMN IF NOT EXISTS appointment_id BIGINT REFERENCES appointments(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_care_tasks_appointment_id
  ON care_tasks(appointment_id)
  WHERE appointment_id IS NOT NULL;
```

### STEP-002 — Repository

Em `modules/careplanner/repository.py`:

```python
async def get_task_by_appointment(
    ctx: TenantContext, appointment_id: int
) -> CareTask | None:
    """Retorna a care_task ativa vinculada ao agendamento, se houver."""
    row = await ctx.db.fetchrow(
        """
        SELECT * FROM care_tasks
        WHERE appointment_id = $1
          AND status NOT IN ('CLOSED','EXPIRED','FAILED')
        ORDER BY created_at DESC LIMIT 1
        """,
        appointment_id,
    )
    return CareTask(**row) if row else None

async def link_task_to_appointment(
    ctx: TenantContext, correlation_id: str, appointment_id: int
) -> None:
    await ctx.db.execute(
        "UPDATE care_tasks SET appointment_id = $1 WHERE correlation_id = $2",
        appointment_id,
        correlation_id,
    )
```

### STEP-003 — Schema e Service

Em `modules/careplanner/contracts.py`, adicionar campo ao `OpenTaskRequest`:

```python
class OpenTaskRequest(BaseModel):
    # campos existentes mantidos
    appointment_id: int | None = None
```

Em `modules/careplanner/services.py`, em `open_task()`:

```python
# Após inserir a task no banco
if request.appointment_id:
    await self.repo.link_task_to_appointment(
        ctx, correlation_id, request.appointment_id
    )
```

### STEP-004 — Endpoint de consulta reversa

Em `modules/careplanner/api/routes.py`:

```python
@router.get("/appointments/{appointment_id}/journey")
async def get_journey_by_appointment(
    appointment_id: int,
    ctx: TenantContext = Depends(get_tenant_context),
    _: UserClaims = Depends(require_roles(["GESTOR", "CLINICO"])),
):
    task = await careplanner_service.repo.get_task_by_appointment(ctx, appointment_id)
    if not task:
        raise HTTPException(404, "Nenhuma jornada ativa para este agendamento")
    return task
```

---

## Fase B — Frontend GestorUI

### STEP-005 — TriggerJourneyModal: campo appointment_id opcional

Em `GestorUI/components/TriggerJourneyModal.tsx`:

```tsx
// Adicionar ao form state
const [appointmentId, setAppointmentId] = useState<number | null>(null)

// Campo opcional no formulário
<NumberInput
  label="Agendamento vinculado (opcional)"
  placeholder="ID do agendamento"
  value={appointmentId ?? ''}
  onChange={(v) => setAppointmentId(v ? Number(v) : null)}
  min={1}
/>

// Incluir no payload do trigger
appointment_id: appointmentId ?? undefined
```

### STEP-006 — CareplannerJourneyDetail: exibir agendamento vinculado

Em `GestorUI/pages/CareplannerJourneyDetail.tsx`, adicionar bloco na timeline
quando `task.appointment_id` estiver preenchido:

```tsx
{task.appointment_id && (
  <Alert icon={<IconCalendar />} color="blue" mt="md">
    Agendamento vinculado:{' '}
    <Anchor href={`/gestor-ui/agendamentos/${task.appointment_id}`} target="_blank">
      #{task.appointment_id}
    </Anchor>
  </Alert>
)}
```

### STEP-007 — AgendamentoDetail: badge de jornada ativa

Em `GestorUI/pages/AgendamentoDetail.tsx` (ou equivalente), adicionar chamada
ao endpoint reverso e exibir badge se houver jornada:

```tsx
const { data: journey } = useQuery({
  queryKey: ['journey-by-appointment', appointmentId],
  queryFn: () => api.get(`/careplanner/appointments/${appointmentId}/journey`),
  retry: false,
})

{journey && (
  <Badge color="teal" leftSection={<IconMessageCircle size={12} />}>
    Jornada CarePlanner ativa
  </Badge>
)}
```

---

## Fase C — Testes

### STEP-008 — Testes Python

`packages/intellicare-core/tests/test_careplanner_appointment.py`:

```python
async def test_link_appointment_to_task(async_client, tenant_ctx):
    """open_task com appointment_id persiste o vínculo."""
    appt_id = await create_test_appointment(tenant_ctx)
    resp = await async_client.post("/careplanner/journeys", json={
        ...,
        "appointment_id": appt_id,
    })
    assert resp.status_code == 200
    cid = resp.json()["correlation_id"]

    task = await repo.get_task_by_correlation(tenant_ctx, cid)
    assert task.appointment_id == appt_id

async def test_get_journey_by_appointment(async_client, tenant_ctx):
    """GET /appointments/{id}/journey retorna a task vinculada."""
    # setup via test anterior
    resp = await async_client.get(f"/careplanner/appointments/{appt_id}/journey")
    assert resp.status_code == 200
    assert resp.json()["correlation_id"] == cid

async def test_get_journey_by_appointment_not_found(async_client):
    resp = await async_client.get("/careplanner/appointments/999999/journey")
    assert resp.status_code == 404
```

---

## Critérios de Aceite

- [ ] Migration 012 aplicada sem erro em `alembic upgrade head` (ou equivalente)
- [ ] `open_task` aceita `appointment_id` opcional e persiste no banco
- [ ] `GET /appointments/{id}/journey` retorna 200 ou 404 correto
- [ ] `TriggerJourneyModal` tem campo opcional de agendamento
- [ ] `CareplannerJourneyDetail` exibe link para agendamento quando vinculado
- [ ] `AgendamentoDetail` exibe badge de jornada ativa quando houver
- [ ] 3 testes passando (link, get, not found)
