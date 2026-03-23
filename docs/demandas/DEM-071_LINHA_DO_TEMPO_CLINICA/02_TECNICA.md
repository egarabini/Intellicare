---
tipo: especificacao-tecnica
demanda: DEM-071
titulo: Linha do Tempo Clínica
---

# DEM-071 — Especificação Técnica

## Mapa de mudanças

| Arquivo | Tipo | O que muda |
|---------|------|-----------|
| `modules/cuidado/routes.py` | Modificar | Novo endpoint `GET /cuidado/patients/{id}/timeline` |
| `modules/cuidado/services.py` | Modificar | `get_patient_timeline()` — query unificada |
| `modules/cuidado/schemas.py` | Modificar | `TimelineEvent`, `TimelineResponse` |
| `frontend/ClinicoUI/src/pages/PatientProfile.tsx` | Modificar | Adicionar aba "Linha do Tempo" |
| `frontend/ClinicoUI/src/components/ClinicalTimeline.tsx` | **Novo** | Componente de timeline com filtros |
| `frontend/ClinicoUI/src/hooks/useTimeline.ts` | **Novo** | Hook para busca paginada com filtros |
| `tests/test_timeline.py` | **Novo** | 4+ testes |

---

## Endpoint

```
GET /cuidado/patients/{patient_id}/timeline
  ?type=all|encounters|notes|prescriptions|journeys  (default: all)
  ?days=30|90|180|all                                 (default: all)
  ?page=1&limit=20
```

**Response:**
```json
{
  "patient_id": "uuid",
  "total": 42,
  "events": [
    {
      "id": "uuid",
      "type": "note",
      "date": "2026-03-15T10:30:00Z",
      "title": "Nota SOAP — Cefaleia",
      "preview": "S: dor em pressão frontal...",
      "metadata": {
        "note_type": "SOAP",
        "encounter_id": "uuid",
        "cid10": null
      }
    },
    {
      "id": "uuid",
      "type": "prescription",
      "date": "2026-03-15T10:35:00Z",
      "title": "Prescrição — R51 Cefaleia",
      "preview": "Dipirona 500mg, Ibuprofeno 400mg",
      "metadata": {
        "cid10_code": "R51",
        "cid10_desc": "Cefaleia",
        "items_count": 2
      }
    },
    {
      "id": "uuid",
      "type": "journey",
      "date": "2026-03-16T09:00:00Z",
      "title": "Jornada CarePlanner — WhatsApp",
      "preview": "Confirmação de retorno",
      "metadata": {
        "channel": "whatsapp",
        "status": "REPLIED"
      }
    }
  ]
}
```

---

## `get_patient_timeline()` — query unificada

```python
async def get_patient_timeline(
    patient_id: str,
    tenant_slug: str,
    type_filter: str = "all",
    days: int | None = None,
    page: int = 1,
    limit: int = 20
) -> TimelineResponse:
    """
    UNION das tabelas: encounters, clinical_notes, prescriptions, journeys
    Todas filtradas por patient_id e ordered by date DESC
    Paginado para performance
    """
```

A query usa `UNION ALL` no PostgreSQL com `date_trunc` para ordenação consistente — não carregar tudo em memória Python.

---

## `ClinicalTimeline.tsx` — estrutura

```tsx
// Ícones por tipo de evento (Mantine UI)
encounter    → IconStethoscope    (azul)
note         → IconNotes          (verde)
prescription → IconPrescription   (roxo)
journey      → IconMessages       (laranja)

// Card de evento
<TimelineItem
  icon={<IconByType type={event.type} />}
  date={formatDate(event.date)}
  title={event.title}
  preview={event.preview}
  onClick={() => navigate(`/encontros/${event.metadata.encounter_id}`)}
/>

// Filtros no topo
<SegmentedControl data={["Todos","Encontros","Notas","Prescrições","Jornadas"]} />
<Select data={["30 dias","90 dias","180 dias","Tudo"]} />
```

---

## Dependências

- Sem migrations novas — usa tabelas existentes (encounters, clinical_notes, prescriptions, journeys)
- Sem dependências externas novas
- `tenant_session(ctx)` para isolamento multi-tenant (padrão V3)
