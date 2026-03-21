# DEM-059 — Portal do Paciente: Acesso a Notas e Jornadas

> **Dev:** CODEX
> **Estimativa:** ~3h
> **Dependência:** DEM-022 (Portal base), DEM-055 (Florence notas), DEM-038 (CarePlanner)
> **Executor Matrix:** todos os novos endpoints → **Worker** (somente leitura)

---

## Contexto

O Portal do Paciente (DEM-022) tem 6 páginas: Dashboard, Agenda, Consultas, Documentos,
Mensagens e Perfil. Hoje o paciente não enxerga suas jornadas CarePlanner nem o resumo
das notas clínicas do seu histórico.

Esta DEM adiciona duas novas seções ao portal:

1. **Minhas Jornadas** — lista de jornadas CarePlanner do paciente com status e canal
2. **Meu Histórico Clínico** — resumo das notas Florence (sem campos SOAP internos —
   apenas o texto livre ou um resumo gerado do SOAP, para não expor terminologia técnica)

---

## Fase A — Backend

### STEP-001 — Endpoints do portal

`modules/portal/api/routes.py` — adicionar:

```python
@router.get("/me/journeys", response_model=list[PatientJourney])
async def my_journeys(
    ctx: TenantContext = Depends(get_tenant_context),
    user: UserClaims = Depends(require_roles(["PACIENTE"])),
    limit: int = Query(20, le=50),
    offset: int = Query(0, ge=0),
):
    return await portal_repo.get_patient_journeys(ctx, user.patient_id, limit, offset)

@router.get("/me/clinical-notes", response_model=list[PatientNote])
async def my_clinical_notes(
    ctx: TenantContext = Depends(get_tenant_context),
    user: UserClaims = Depends(require_roles(["PACIENTE"])),
    limit: int = Query(20, le=50),
):
    return await portal_repo.get_patient_notes_summary(ctx, user.patient_id, limit)
```

### STEP-002 — Contracts do portal

`modules/portal/contracts.py` — adicionar:

```python
class PatientJourney(BaseModel):
    correlation_id: str
    channel: str               # WHATSAPP | EMAIL | SMS | ROCKETCHAT
    status: str                # OPEN | DISPATCHED | SENT | REPLIED | CLOSED | EXPIRED
    template_name: str | None
    opened_at: datetime
    closed_at: datetime | None

class PatientNote(BaseModel):
    encounter_date: datetime
    professional_name: str
    summary: str               # free_text se FREE; concatenação "S: ... P: ..." se SOAP
    # NÃO expõe soap_a (avaliação interna) nem campos sensíveis
```

### STEP-003 — Repository do portal

`modules/portal/repository.py` — adicionar:

```python
async def get_patient_journeys(
    ctx: TenantContext, patient_id: int, limit: int, offset: int
) -> list[PatientJourney]:
    rows = await ctx.db.fetch(
        """
        SELECT ct.correlation_id, ct.channel, ct.status,
               ct.template_name, ct.created_at AS opened_at, ct.closed_at
        FROM care_tasks ct
        WHERE ct.patient_id = $1
        ORDER BY ct.created_at DESC
        LIMIT $2 OFFSET $3
        """,
        patient_id, limit, offset,
    )
    return [PatientJourney(**r) for r in rows]

async def get_patient_notes_summary(
    ctx: TenantContext, patient_id: int, limit: int
) -> list[PatientNote]:
    rows = await ctx.db.fetch(
        """
        SELECT
            e.scheduled_at AS encounter_date,
            cn.author_name AS professional_name,
            cn.note_type,
            cn.free_text,
            cn.soap_s,
            cn.soap_p
        FROM clinical_notes cn
        JOIN encounters e ON e.id = cn.encounter_id
        WHERE cn.patient_id = $1
        ORDER BY cn.created_at DESC
        LIMIT $2
        """,
        patient_id, limit,
    )
    notes = []
    for r in rows:
        if r["note_type"] == "FREE":
            summary = r["free_text"] or ""
        else:
            # Expõe só Subjetivo e Plano — não Avaliação (campo sensível)
            parts = []
            if r["soap_s"]:
                parts.append(f"Queixa: {r['soap_s']}")
            if r["soap_p"]:
                parts.append(f"Orientações: {r['soap_p']}")
            summary = " | ".join(parts) if parts else "Consulta registrada."
        notes.append(PatientNote(
            encounter_date=r["encounter_date"],
            professional_name=r["professional_name"],
            summary=summary,
        ))
    return notes
```

---

## Fase B — Frontend PacienteUI

### STEP-004 — Página MinhasJornadas

`PacienteUI/pages/MinhasJornadas.tsx`:

```tsx
// Lista paginada de jornadas com:
// - Badge de canal (ícone WA/Email/SMS/RC)
// - Badge de status com cor (OPEN=azul, REPLIED=verde, EXPIRED=cinza)
// - Data de abertura e fechamento
// - Nome do template se disponível
```

### STEP-005 — Página MeuHistorico

`PacienteUI/pages/MeuHistorico.tsx`:

```tsx
// Timeline de notas clínicas com:
// - Data da consulta
// - Nome do profissional
// - Resumo (sem terminologia SOAP interna)
// - Sem campos soap_a (avaliação) — privacidade clínica
```

### STEP-006 — Navegação

`PacienteUI/AppShell.tsx` — adicionar links no menu:

```tsx
<NavLink
  label="Minhas Jornadas"
  leftSection={<IconMessageCircle size={16} />}
  href="/paciente-ui/jornadas"
/>
<NavLink
  label="Histórico Clínico"
  leftSection={<IconClipboardHeart size={16} />}
  href="/paciente-ui/historico"
/>
```

---

## Fase C — Testes

### STEP-007 — Testes Python

`packages/intellicare-core/tests/test_portal_notas.py`:

```python
async def test_my_journeys_empty(async_client_paciente):
    resp = await async_client_paciente.get("/portal/me/journeys")
    assert resp.status_code == 200
    assert resp.json() == []

async def test_my_clinical_notes_no_soap_a(async_client_paciente, seed_note_soap):
    """Campo soap_a (avaliação) não deve aparecer no resumo do paciente."""
    resp = await async_client_paciente.get("/portal/me/clinical-notes")
    assert resp.status_code == 200
    notes = resp.json()
    assert len(notes) > 0
    for note in notes:
        assert "soap_a" not in note
        assert "Avaliação" not in note.get("summary", "")

async def test_portal_requires_paciente_role(async_client_gestor):
    """Gestor não acessa endpoints do portal do paciente."""
    resp = await async_client_gestor.get("/portal/me/journeys")
    assert resp.status_code == 403
```

---

## Critérios de Aceite

- [ ] `GET /portal/me/journeys` retorna jornadas paginadas do paciente autenticado
- [ ] `GET /portal/me/clinical-notes` retorna resumo sem `soap_a` exposto
- [ ] Página "Minhas Jornadas" visível no PacienteUI com badges de canal e status
- [ ] Página "Histórico Clínico" com timeline de consultas
- [ ] Links no menu do portal
- [ ] 3 testes passando (empty, no soap_a, role guard)

---

## Executor Matrix

| Componente | Categoria | Justificativa |
|---|---|---|
| `get_patient_journeys()` | Worker | Somente leitura, filtrado por patient_id autenticado |
| `get_patient_notes_summary()` | Worker | Somente leitura; exposição controlada (sem soap_a) |
| `MinhasJornadas` / `MeuHistorico` | Worker | UI de consulta sem side effect |

---

## Nota de Privacidade

O campo `soap_a` (Avaliação/Diagnóstico) é omitido intencionalmente do resumo
do paciente. A avaliação diagnóstica é informação clínica interna — o paciente
recebe apenas a queixa registrada e as orientações do plano. Esse comportamento
deve ser documentado e auditável.
