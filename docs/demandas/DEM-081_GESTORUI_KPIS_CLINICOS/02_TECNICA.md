---
tipo: especificacao-tecnica
demanda: DEM-081
titulo: GestorUI KPIs Clínicos
---

# DEM-081 — Especificação Técnica

## Mapa de mudanças

| Arquivo | Tipo | O que muda |
|---------|------|-----------|
| `modules/admin/kpis.py` | **Novo** | `get_clinical_kpis(tenant, start, end, professional_id?)` |
| `modules/admin/routes.py` | Modificar | `GET /admin/kpis/clinical?start=&end=&professional_id=` |
| `modules/admin/schemas.py` | Modificar | `ClinicalKPIsResponse` |
| `frontend/GestorUI/src/pages/IndicadoresPage.tsx` | **Novo** | Página KPIs com cards + gráficos Recharts |
| `frontend/GestorUI/src/hooks/useClinicalKPIs.ts` | **Novo** | Hook react-query |
| `frontend/GestorUI/src/App.tsx` | Modificar | Rota `/indicadores` + NavLink no menu |
| `packages/intellicare-core/tests/test_clinical_kpis.py` | **Novo** | 3+ testes |

---

## Endpoint

```
GET /admin/kpis/clinical?start=2026-04-01&end=2026-04-30&professional_id=UUID (opcional)
Authorization: Bearer {gestor_token}

Response 200: ClinicalKPIsResponse
```

---

## `modules/admin/kpis.py`

```python
def get_clinical_kpis(
    ctx,
    start: date,
    end: date,
    professional_id: UUID | None = None,
) -> ClinicalKPIsResponse:
    """
    Agrega KPIs clínicos do tenant em uma única query por tabela.
    Usa tenant_session(ctx) para isolamento multi-tenant.
    """
    with tenant_session(ctx) as db:
        prof_filter = "AND professional_id = :pid" if professional_id else ""
        params = {"start": start, "end": end, "pid": professional_id}

        encounters = db.execute(text(f"""
            SELECT COUNT(*) FROM encounters
            WHERE status = 'closed'
              AND opened_at::date BETWEEN :start AND :end
              {prof_filter}
        """), params).scalar()

        notes = db.execute(text(f"""
            SELECT COUNT(*) FROM clinical_notes
            WHERE created_at::date BETWEEN :start AND :end
              {prof_filter}
        """), params).scalar()

        prescriptions = db.execute(text(f"""
            SELECT COUNT(*) FROM prescriptions
            WHERE created_at::date BETWEEN :start AND :end
              {prof_filter}
        """), params).scalar()

        # Interações: log da tabela de audit (ou contagem via campo na prescrição)
        # Simplificação v1: contar prescrições com campo interaction_warnings_count > 0
        interactions = db.execute(text("""
            SELECT COUNT(*) FROM prescriptions
            WHERE interaction_warnings_count > 0
              AND created_at::date BETWEEN :start AND :end
        """), {"start": start, "end": end}).scalar()

        journeys = db.execute(text("""
            SELECT status, COUNT(*) FROM journeys
            WHERE created_at::date BETWEEN :start AND :end
            GROUP BY status
        """), {"start": start, "end": end}).fetchall()

        # Top médicos por prescrições
        top_professionals = db.execute(text(f"""
            SELECT p.name, COUNT(pr.id) as total
            FROM prescriptions pr
            JOIN professionals p ON p.id = pr.professional_id
            WHERE pr.created_at::date BETWEEN :start AND :end
            GROUP BY p.name ORDER BY total DESC LIMIT 5
        """), {"start": start, "end": end}).fetchall()

        # Série temporal de interações por dia
        interactions_by_day = db.execute(text("""
            SELECT created_at::date as day, COUNT(*) as total
            FROM prescriptions
            WHERE interaction_warnings_count > 0
              AND created_at::date BETWEEN :start AND :end
            GROUP BY day ORDER BY day
        """), {"start": start, "end": end}).fetchall()

    return ClinicalKPIsResponse(
        encounters=encounters,
        notes=notes,
        prescriptions=prescriptions,
        interactions_detected=interactions,
        journeys={r.status: r.count for r in journeys},
        top_professionals=[{"name": r.name, "total": r.total} for r in top_professionals],
        interactions_by_day=[{"day": str(r.day), "total": r.total} for r in interactions_by_day],
    )
```

> ⚠️ **Pré-requisito:** migration 020 adiciona coluna `interaction_warnings_count INTEGER DEFAULT 0` em `prescriptions`. Atualizar `generate_receituario()` em DEM-077 para persistir a contagem quando `/check-interactions` for chamado.

---

## Schema

```python
class ClinicalKPIsResponse(BaseModel):
    encounters: int
    notes: int
    prescriptions: int
    interactions_detected: int
    journeys: dict[str, int]          # {"OPEN": 5, "CLOSED": 12, "EXPIRED": 2}
    top_professionals: list[dict]      # [{"name": "Dr. Silva", "total": 23}]
    interactions_by_day: list[dict]    # [{"day": "2026-04-15", "total": 3}]
```

---

## Frontend — `IndicadoresPage.tsx`

Componentes Mantine + Recharts:
- `SimpleGrid` com 6 `StatCard` (número + label + ícone)
- `BarChart` Recharts — Top Médicos (prescrições)
- `LineChart` Recharts — Interações por dia
- `Select` Mantine — filtro período (7/30/90 dias)
- `Select` Mantine — filtro médico (lista de professionals do tenant)

---

## Migration 020

```sql
ALTER TABLE {schema}.prescriptions
  ADD COLUMN IF NOT EXISTS interaction_warnings_count INTEGER NOT NULL DEFAULT 0;
```

Adicionar em `db/tenant_migrations/020_prescription_interaction_count.sql`.

---

## Testes

| Teste | Cenário |
|-------|---------|
| `test_kpis_returns_correct_counts` | Tenant com 5 encounters + 3 prescriptions → KPIs refletem contagens corretas |
| `test_kpis_filtered_by_professional` | Filtro por `professional_id` retorna apenas dados do profissional |
| `test_kpis_empty_period` | Período sem dados → todos os campos retornam 0, sem erro |
